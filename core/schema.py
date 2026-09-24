import re


class MethodSchemaValidator:
    REQUIRED_FIELDS = [
        "id",
        "name",
        "language",
        "architectures",
        "requires_payload",
        "payload_types",
        "sources",
        "output_name"
    ]

    SUPPORTED_ARCHITECTURES = {
        "x64",
        "x86"
    }

    SUPPORTED_LANGUAGES = {
        "c",
        "cpp"
    }

    SUPPORTED_BUILD_TYPES = {
        "release",
        "debug"
    }

    SUPPORTED_PARAMETER_TYPES = {
        "str",
        "int",
        "float",
        "bool"
    }

    SUPPORTED_PARAMETER_RENDERERS = {
        "raw",
        "c_string"
    }

    SUPPORTED_RUNTIME_ARGUMENT_TYPES = {
        "str",
        "int",
        "float",
        "bool",
        "hex",
        "path"
    }

    SUPPORTED_PAYLOAD_TYPES = {
        "raw",
        "text",
        "json",
        "pe"
    }

    SUPPORTED_PAYLOAD_TRANSFORMS = {
        "copy",
        "base64",
        "hex"
    }

    SUPPORTED_TECHNIQUE_ROLES = {
        "technique",
        "helper",
        "inspect"
    }

    SUPPORTED_TECHNIQUE_RUNTIMES = {
        "native",
        "managed",
        "script",
        "kernel",
        "mixed"
    }

    SUPPORTED_TECHNIQUE_PRIVILEGES = {
        "user",
        "admin",
        "system",
        "driver",
        "varies"
    }

    SUPPORTED_TECHNIQUE_VALIDATION = {
        "planned",
        "build-tested",
        "runtime-tested"
    }

    TECHNIQUE_ALIAS = re.compile(
        r"^[a-z][a-z0-9-]*$"
    )

    PARAMETER_NAME = re.compile(
        r"^[A-Za-z_][A-Za-z0-9_]*$"
    )

    def _validate_technique(
        self,
        method,
        errors
    ):
        technique = method.get(
            "technique"
        )

        if technique is None:
            return

        if not isinstance(
            technique,
            dict
        ):
            errors.append(
                "technique must be an object"
            )
            return

        required_fields = [
            "alias",
            "category",
            "role",
            "quick",
            "runtime",
            "privilege",
            "validation"
        ]

        for field in required_fields:
            if field not in technique:
                errors.append(
                    f"technique missing required field: {field}"
                )

        alias = technique.get(
            "alias"
        )

        if (
            alias is not None
            and (
                not isinstance(
                    alias,
                    str
                )
                or not self.TECHNIQUE_ALIAS.match(
                    alias
                )
            )
        ):
            errors.append(
                "technique.alias must be a lowercase "
                "CLI-safe alias"
            )

        category = technique.get(
            "category"
        )

        if (
            category is not None
            and (
                not isinstance(
                    category,
                    str
                )
                or not category.strip()
            )
        ):
            errors.append(
                "technique.category must be a "
                "non-empty string"
            )

        role = technique.get(
            "role"
        )

        if (
            role is not None
            and role not in self.SUPPORTED_TECHNIQUE_ROLES
        ):
            errors.append(
                f"Unsupported technique role: {role}"
            )

        quick = technique.get(
            "quick"
        )

        if (
            quick is not None
            and not isinstance(
                quick,
                bool
            )
        ):
            errors.append(
                "technique.quick must be true or false"
            )

        runtime = technique.get(
            "runtime"
        )

        if (
            runtime is not None
            and runtime
            not in self.SUPPORTED_TECHNIQUE_RUNTIMES
        ):
            errors.append(
                f"Unsupported technique runtime: {runtime}"
            )

        privilege = technique.get(
            "privilege"
        )

        if (
            privilege is not None
            and privilege
            not in self.SUPPORTED_TECHNIQUE_PRIVILEGES
        ):
            errors.append(
                f"Unsupported technique privilege: {privilege}"
            )

        validation = technique.get(
            "validation"
        )

        if (
            validation is not None
            and validation
            not in self.SUPPORTED_TECHNIQUE_VALIDATION
        ):
            errors.append(
                f"Unsupported technique validation: {validation}"
            )

    def _validate_payload_contract(
        self,
        method,
        errors
    ):
        contract = method.get(
            "payload_contract"
        )

        if contract is None:
            return

        if not isinstance(
            contract,
            dict
        ):
            errors.append(
                "payload_contract must be an object"
            )
            return

        required = contract.get(
            "required"
        )

        if not isinstance(
            required,
            bool
        ):
            errors.append(
                "payload_contract.required must "
                "be true or false"
            )

        elif required != method.get(
            "requires_payload"
        ):
            errors.append(
                "payload_contract.required must "
                "match requires_payload"
            )

        types = contract.get(
            "types"
        )

        if not isinstance(
            types,
            list
        ):
            errors.append(
                "payload_contract.types must be "
                "a list"
            )

        else:
            if required is True and not types:
                errors.append(
                    "payload_contract.required=true "
                    "but types is empty"
                )

            if required is False and types:
                errors.append(
                    "payload_contract.required=false "
                    "but types is not empty"
                )

            if (
                types
                != method.get(
                    "payload_types"
                )
            ):
                errors.append(
                    "payload_contract.types must "
                    "match payload_types"
                )

            for payload_type in types:
                if (
                    payload_type
                    not in self.SUPPORTED_PAYLOAD_TYPES
                ):
                    errors.append(
                        f"Unsupported payload type: "
                        f"{payload_type}"
                    )

        transforms = contract.get(
            "transforms",
            [
                "copy"
            ]
        )

        if (
            not isinstance(
                transforms,
                list
            )
            or not transforms
        ):
            errors.append(
                "payload_contract.transforms must "
                "be a non-empty list"
            )

        else:
            for transform in transforms:
                if (
                    transform
                    not in self.SUPPORTED_PAYLOAD_TRANSFORMS
                ):
                    errors.append(
                        f"Unsupported payload transform: "
                        f"{transform}"
                    )

        default_transform = contract.get(
            "default_transform",
            "copy"
        )

        if (
            isinstance(
                transforms,
                list
            )
            and default_transform
            not in transforms
        ):
            errors.append(
                "payload_contract.default_transform "
                "must be listed in transforms"
            )

        minimum = contract.get(
            "min_size_bytes",
            1
        )

        maximum = contract.get(
            "max_size_bytes",
            64 * 1024 * 1024
        )

        if (
            not isinstance(
                minimum,
                int
            )
            or isinstance(
                minimum,
                bool
            )
            or minimum < 0
        ):
            errors.append(
                "payload_contract.min_size_bytes "
                "must be a non-negative integer"
            )

        if (
            not isinstance(
                maximum,
                int
            )
            or isinstance(
                maximum,
                bool
            )
            or maximum < 1
        ):
            errors.append(
                "payload_contract.max_size_bytes "
                "must be a positive integer"
            )

        if (
            isinstance(
                minimum,
                int
            )
            and not isinstance(
                minimum,
                bool
            )
            and isinstance(
                maximum,
                int
            )
            and not isinstance(
                maximum,
                bool
            )
            and minimum > maximum
        ):
            errors.append(
                "payload_contract.min_size_bytes "
                "cannot be greater than "
                "max_size_bytes"
            )

    def _validate_parameters(
        self,
        method,
        errors
    ):
        parameters = method.get(
            "parameters",
            {}
        )

        if not isinstance(
            parameters,
            dict
        ):
            errors.append(
                "parameters must be an object"
            )
            return

        for name, spec in parameters.items():
            prefix = (
                f"parameters.{name}"
            )

            if (
                not isinstance(
                    name,
                    str
                )
                or not self.PARAMETER_NAME.match(
                    name
                )
            ):
                errors.append(
                    f"Invalid parameter name: "
                    f"{name}"
                )
                continue

            if not isinstance(
                spec,
                dict
            ):
                errors.append(
                    f"{prefix} must be an object"
                )
                continue

            parameter_type = spec.get(
                "type",
                "str"
            )

            if (
                parameter_type
                not in self.SUPPORTED_PARAMETER_TYPES
            ):
                errors.append(
                    f"{prefix}.type is unsupported: "
                    f"{parameter_type}"
                )

            required = spec.get(
                "required",
                False
            )

            if not isinstance(
                required,
                bool
            ):
                errors.append(
                    f"{prefix}.required must be "
                    "true or false"
                )

            render = spec.get(
                "render",
                "raw"
            )

            if (
                render
                not in self.SUPPORTED_PARAMETER_RENDERERS
            ):
                errors.append(
                    f"{prefix}.render is unsupported: "
                    f"{render}"
                )

            description = spec.get(
                "description"
            )

            if (
                description is not None
                and not isinstance(
                    description,
                    str
                )
            ):
                errors.append(
                    f"{prefix}.description must "
                    "be a string"
                )

            choices = spec.get(
                "choices"
            )

            if (
                choices is not None
                and (
                    not isinstance(
                        choices,
                        list
                    )
                    or not choices
                )
            ):
                errors.append(
                    f"{prefix}.choices must be "
                    "a non-empty list"
                )

            minimum = spec.get(
                "min"
            )

            maximum = spec.get(
                "max"
            )

            if (
                minimum is not None
                and not isinstance(
                    minimum,
                    (
                        int,
                        float
                    )
                )
            ):
                errors.append(
                    f"{prefix}.min must be numeric"
                )

            if (
                maximum is not None
                and not isinstance(
                    maximum,
                    (
                        int,
                        float
                    )
                )
            ):
                errors.append(
                    f"{prefix}.max must be numeric"
                )

            if (
                isinstance(
                    minimum,
                    (
                        int,
                        float
                    )
                )
                and isinstance(
                    maximum,
                    (
                        int,
                        float
                    )
                )
                and minimum > maximum
            ):
                errors.append(
                    f"{prefix}.min cannot be "
                    "greater than max"
                )

    def _validate_runtime_arguments(
        self,
        method,
        errors
    ):
        runtime_arguments = method.get(
            "runtime_arguments",
            []
        )

        if not isinstance(
            runtime_arguments,
            list
        ):
            errors.append(
                "runtime_arguments must be a list"
            )
            return

        names = set()

        for index, argument in enumerate(
            runtime_arguments
        ):
            prefix = (
                f"runtime_arguments[{index}]"
            )

            if not isinstance(
                argument,
                dict
            ):
                errors.append(
                    f"{prefix} must be an object"
                )
                continue

            name = argument.get(
                "name"
            )

            if (
                not isinstance(
                    name,
                    str
                )
                or not name.strip()
            ):
                errors.append(
                    f"{prefix}.name must be a "
                    "non-empty string"
                )

            elif name in names:
                errors.append(
                    f"Duplicate runtime argument: "
                    f"{name}"
                )

            else:
                names.add(
                    name
                )

            argument_type = argument.get(
                "type",
                "str"
            )

            if (
                argument_type
                not in self.SUPPORTED_RUNTIME_ARGUMENT_TYPES
            ):
                errors.append(
                    f"{prefix}.type is unsupported: "
                    f"{argument_type}"
                )

            required = argument.get(
                "required",
                True
            )

            if not isinstance(
                required,
                bool
            ):
                errors.append(
                    f"{prefix}.required must be "
                    "true or false"
                )

            description = argument.get(
                "description"
            )

            if (
                description is not None
                and not isinstance(
                    description,
                    str
                )
            ):
                errors.append(
                    f"{prefix}.description must "
                    "be a string"
                )

    def _validate_build_types(
        self,
        method,
        errors
    ):
        build_types = method.get(
            "build_types"
        )

        if build_types is None:
            return

        if not isinstance(
            build_types,
            list
        ):
            errors.append(
                "build_types must be a list"
            )
            return

        if not build_types:
            errors.append(
                "build_types must contain at "
                "least one build type"
            )
            return

        for build_type in build_types:
            if (
                build_type
                not in self.SUPPORTED_BUILD_TYPES
            ):
                errors.append(
                    f"Unsupported build type: "
                    f"{build_type}"
                )

    def validate(self, method):
        errors = []

        for field in self.REQUIRED_FIELDS:
            if field not in method:
                errors.append(
                    f"Missing required field: {field}"
                )

        if errors:
            return errors

        method_id = method.get(
            "id"
        )

        if (
            not isinstance(
                method_id,
                str
            )
            or not method_id.strip()
        ):
            errors.append(
                "id must be a non-empty string"
            )

        name = method.get(
            "name"
        )

        if (
            not isinstance(
                name,
                str
            )
            or not name.strip()
        ):
            errors.append(
                "name must be a non-empty string"
            )

        language = method.get(
            "language"
        )

        if (
            language
            not in self.SUPPORTED_LANGUAGES
        ):
            errors.append(
                f"Unsupported language: "
                f"{language}"
            )

        architectures = method.get(
            "architectures"
        )

        if not isinstance(
            architectures,
            list
        ):
            errors.append(
                "architectures must be a list"
            )

        elif not architectures:
            errors.append(
                "architectures must contain at "
                "least one architecture"
            )

        else:
            for architecture in architectures:
                if (
                    architecture
                    not in self.SUPPORTED_ARCHITECTURES
                ):
                    errors.append(
                        f"Unsupported architecture: "
                        f"{architecture}"
                    )

        requires_payload = method.get(
            "requires_payload"
        )

        if not isinstance(
            requires_payload,
            bool
        ):
            errors.append(
                "requires_payload must be "
                "true or false"
            )

        payload_types = method.get(
            "payload_types"
        )

        if not isinstance(
            payload_types,
            list
        ):
            errors.append(
                "payload_types must be a list"
            )

        else:
            for payload_type in payload_types:
                if (
                    payload_type
                    not in self.SUPPORTED_PAYLOAD_TYPES
                ):
                    errors.append(
                        f"Unsupported payload type: "
                        f"{payload_type}"
                    )

            if (
                requires_payload is True
                and not payload_types
            ):
                errors.append(
                    "requires_payload=true but "
                    "payload_types is empty"
                )

            if (
                requires_payload is False
                and payload_types
            ):
                errors.append(
                    "requires_payload=false but "
                    "payload_types is not empty"
                )

        sources = method.get(
            "sources"
        )

        if not isinstance(
            sources,
            list
        ):
            errors.append(
                "sources must be a list"
            )

        elif not sources:
            errors.append(
                "sources must contain at "
                "least one file"
            )

        else:
            outputs = set()
            compile_count = 0

            for index, source in enumerate(
                sources
            ):
                prefix = (
                    f"sources[{index}]"
                )

                if not isinstance(
                    source,
                    dict
                ):
                    errors.append(
                        f"{prefix} must be "
                        "an object"
                    )
                    continue

                template = source.get(
                    "template"
                )

                output = source.get(
                    "output"
                )

                compile_file = source.get(
                    "compile"
                )

                if (
                    not isinstance(
                        template,
                        str
                    )
                    or not template.strip()
                ):
                    errors.append(
                        f"{prefix}.template must "
                        "be a non-empty string"
                    )

                if (
                    not isinstance(
                        output,
                        str
                    )
                    or not output.strip()
                ):
                    errors.append(
                        f"{prefix}.output must "
                        "be a non-empty string"
                    )

                elif output in outputs:
                    errors.append(
                        f"Duplicate source output: "
                        f"{output}"
                    )

                else:
                    outputs.add(
                        output
                    )

                if not isinstance(
                    compile_file,
                    bool
                ):
                    errors.append(
                        f"{prefix}.compile must "
                        "be true or false"
                    )

                elif compile_file:
                    compile_count += 1

            if compile_count == 0:
                errors.append(
                    "At least one source must "
                    "have compile=true"
                )

        output_name = method.get(
            "output_name"
        )

        if (
            not isinstance(
                output_name,
                str
            )
            or not output_name.strip()
        ):
            errors.append(
                "output_name must be a "
                "non-empty string"
            )

        self._validate_technique(
            method,
            errors
        )

        self._validate_payload_contract(
            method,
            errors
        )

        self._validate_parameters(
            method,
            errors
        )

        self._validate_runtime_arguments(
            method,
            errors
        )

        self._validate_build_types(
            method,
            errors
        )

        return errors
