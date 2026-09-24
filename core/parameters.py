import re


class ParameterResolver:
    SUPPORTED_TYPES = {
        "str",
        "int",
        "float",
        "bool",
    }

    TRUE_VALUES = {
        "1",
        "true",
        "yes",
        "on",
    }

    FALSE_VALUES = {
        "0",
        "false",
        "no",
        "off",
    }

    PARAMETER_NAME = re.compile(
        r"^[A-Za-z_][A-Za-z0-9_]*$"
    )

    def parse_cli(
        self,
        items
    ):
        values = {}
        errors = []

        for item in items or []:
            if "=" not in item:
                errors.append(
                    f"Invalid --set value '{item}'. "
                    "Expected KEY=VALUE"
                )
                continue

            key, value = item.split(
                "=",
                1
            )

            key = key.strip()

            if not key:
                errors.append(
                    f"Invalid --set value '{item}'. "
                    "Parameter name is empty"
                )
                continue

            if not self.PARAMETER_NAME.match(
                key
            ):
                errors.append(
                    f"Invalid parameter name "
                    f"'{key}'"
                )
                continue

            if key in values:
                errors.append(
                    f"Parameter '{key}' was "
                    "specified more than once"
                )
                continue

            values[key] = value

        return (
            values,
            errors
        )

    def _coerce(
        self,
        name,
        value,
        parameter_type
    ):
        if parameter_type == "str":
            if isinstance(
                value,
                str
            ):
                return value

            return str(
                value
            )

        if parameter_type == "int":
            if isinstance(
                value,
                bool
            ):
                raise ValueError(
                    f"Parameter '{name}' "
                    "must be an integer"
                )

            if isinstance(
                value,
                int
            ):
                return value

            try:
                return int(
                    str(value),
                    0
                )

            except (
                TypeError,
                ValueError
            ) as exc:
                raise ValueError(
                    f"Parameter '{name}' "
                    "must be an integer"
                ) from exc

        if parameter_type == "float":
            if isinstance(
                value,
                bool
            ):
                raise ValueError(
                    f"Parameter '{name}' "
                    "must be a number"
                )

            if isinstance(
                value,
                (
                    int,
                    float
                )
            ):
                return float(
                    value
                )

            try:
                return float(
                    str(value)
                )

            except (
                TypeError,
                ValueError
            ) as exc:
                raise ValueError(
                    f"Parameter '{name}' "
                    "must be a number"
                ) from exc

        if parameter_type == "bool":
            if isinstance(
                value,
                bool
            ):
                return value

            normalized = str(
                value
            ).strip().lower()

            if normalized in (
                self.TRUE_VALUES
            ):
                return True

            if normalized in (
                self.FALSE_VALUES
            ):
                return False

            raise ValueError(
                f"Parameter '{name}' "
                "must be a boolean "
                "(true/false, yes/no, on/off, 1/0)"
            )

        raise ValueError(
            f"Unsupported parameter type "
            f"'{parameter_type}' for "
            f"'{name}'"
        )

    def _validate_value(
        self,
        name,
        value,
        spec
    ):
        errors = []

        choices = spec.get(
            "choices"
        )

        if (
            choices is not None
            and value not in choices
        ):
            errors.append(
                f"Parameter '{name}' must be "
                "one of: "
                + ", ".join(
                    str(choice)
                    for choice in choices
                )
            )

        minimum = spec.get(
            "min"
        )

        maximum = spec.get(
            "max"
        )

        if (
            minimum is not None
            and value is not None
        ):
            try:
                if value < minimum:
                    errors.append(
                        f"Parameter '{name}' must "
                        f"be >= {minimum}"
                    )

            except TypeError:
                errors.append(
                    f"Parameter '{name}' cannot "
                    "be compared with its min value"
                )

        if (
            maximum is not None
            and value is not None
        ):
            try:
                if value > maximum:
                    errors.append(
                        f"Parameter '{name}' must "
                        f"be <= {maximum}"
                    )

            except TypeError:
                errors.append(
                    f"Parameter '{name}' cannot "
                    "be compared with its max value"
                )

        return errors

    def resolve(
        self,
        method,
        preset,
        cli_items=None
    ):
        specs = method.get(
            "parameters",
            {}
        )

        if not isinstance(
            specs,
            dict
        ):
            return (
                {},
                [
                    "Method parameters contract "
                    "must be an object"
                ]
            )

        preset_values = preset.get(
            "parameters",
            {}
        )

        if not isinstance(
            preset_values,
            dict
        ):
            return (
                {},
                [
                    "Preset parameters must be "
                    "an object"
                ]
            )

        cli_values, errors = (
            self.parse_cli(
                cli_items
            )
        )

        known = set(
            specs
        )

        for source_name, source_values in (
            (
                "preset",
                preset_values
            ),
            (
                "command line",
                cli_values
            )
        ):
            for key in source_values:
                if key not in known:
                    errors.append(
                        f"Unknown parameter "
                        f"'{key}' in {source_name}"
                    )

        resolved = {}

        for name, spec in specs.items():
            parameter_type = spec.get(
                "type",
                "str"
            )

            required = spec.get(
                "required",
                False
            )

            has_value = False
            raw_value = None

            if name in cli_values:
                raw_value = cli_values[
                    name
                ]
                has_value = True

            elif name in preset_values:
                raw_value = preset_values[
                    name
                ]
                has_value = True

            elif "default" in spec:
                raw_value = spec[
                    "default"
                ]
                has_value = True

            if not has_value:
                if required:
                    errors.append(
                        f"Required parameter "
                        f"'{name}' is missing"
                    )

                resolved[
                    name
                ] = None
                continue

            try:
                value = self._coerce(
                    name=name,
                    value=raw_value,
                    parameter_type=parameter_type
                )

            except ValueError as exc:
                errors.append(
                    str(exc)
                )
                resolved[
                    name
                ] = None
                continue

            errors.extend(
                self._validate_value(
                    name=name,
                    value=value,
                    spec=spec
                )
            )

            resolved[
                name
            ] = value

        return (
            resolved,
            errors
        )
