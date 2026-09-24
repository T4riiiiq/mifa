class CompatibilityChecker:
    SUPPORTED_BUILD_TYPES = {
        "release",
        "debug"
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

    def _payload_contract(
        self,
        method
    ):
        contract = method.get(
            "payload_contract"
        )

        if contract is None:
            return {
                "required":
                    method.get(
                        "requires_payload",
                        False
                    ),

                "types":
                    list(
                        method.get(
                            "payload_types",
                            []
                        )
                    ),

                "transforms": [
                    "copy"
                ],

                "default_transform":
                    "copy"
            }

        return {
            "required":
                contract.get(
                    "required",
                    method.get(
                        "requires_payload",
                        False
                    )
                ),

            "types":
                list(
                    contract.get(
                        "types",
                        method.get(
                            "payload_types",
                            []
                        )
                    )
                ),

            "transforms":
                list(
                    contract.get(
                        "transforms",
                        [
                            "copy"
                        ]
                    )
                ),

            "default_transform":
                contract.get(
                    "default_transform",
                    "copy"
                )
        }

    def validate_preset(
        self,
        method,
        preset,
        parameter_errors=None
    ):
        errors = []

        architecture = preset.get(
            "architecture"
        )

        supported_arch = method.get(
            "architectures",
            []
        )

        if architecture not in supported_arch:
            errors.append(
                f"Architecture '{architecture}' "
                f"is not supported by method "
                f"'{method.get('id')}'"
            )

        build_type = preset.get(
            "build_type",
            "release"
        )

        method_build_types = method.get(
            "build_types",
            [
                "release",
                "debug"
            ]
        )

        if (
            build_type
            not in self.SUPPORTED_BUILD_TYPES
        ):
            errors.append(
                f"Unsupported build type: "
                f"'{build_type}'"
            )

        elif build_type not in method_build_types:
            errors.append(
                f"Build type '{build_type}' "
                f"is not supported by method "
                f"'{method.get('id')}'"
            )

        if parameter_errors:
            errors.extend(
                parameter_errors
            )

        return errors

    def validate(
        self,
        method,
        preset,
        payload_path=None,
        payload_type=None,
        payload_transform=None,
        parameter_errors=None
    ):
        errors = self.validate_preset(
            method=method,
            preset=preset,
            parameter_errors=parameter_errors
        )

        contract = self._payload_contract(
            method
        )

        requires_payload = contract[
            "required"
        ]

        accepted_payload_types = (
            contract[
                "types"
            ]
        )

        accepted_transforms = (
            contract[
                "transforms"
            ]
        )

        if (
            requires_payload
            and payload_path is None
        ):
            errors.append(
                "This method requires a payload"
            )

        if (
            not requires_payload
            and payload_path is not None
        ):
            errors.append(
                "This method does not accept "
                "a payload"
            )

        if (
            payload_path is None
            and payload_type is not None
        ):
            errors.append(
                "Payload type was specified "
                "without a payload"
            )

        if (
            payload_path is None
            and payload_transform is not None
        ):
            errors.append(
                "Payload transform was specified "
                "without a payload"
            )

        if payload_path is not None:
            if payload_type is None:
                errors.append(
                    "Payload type must be "
                    "specified"
                )

            elif (
                payload_type
                not in accepted_payload_types
            ):
                errors.append(
                    f"Payload type "
                    f"'{payload_type}' is not "
                    f"supported by method "
                    f"'{method.get('id')}'"
                )

            elif (
                payload_type
                not in self.SUPPORTED_PAYLOAD_TYPES
            ):
                errors.append(
                    f"Payload type "
                    f"'{payload_type}' is not "
                    "supported by the Mifa "
                    "payload engine"
                )

            selected_transform = (
                payload_transform
                or contract[
                    "default_transform"
                ]
            )

            if (
                selected_transform
                not in accepted_transforms
            ):
                errors.append(
                    f"Payload transform "
                    f"'{selected_transform}' is not "
                    f"supported by method "
                    f"'{method.get('id')}'"
                )

            elif (
                selected_transform
                not in self.SUPPORTED_PAYLOAD_TRANSFORMS
            ):
                errors.append(
                    f"Payload transform "
                    f"'{selected_transform}' is not "
                    "supported by the Mifa "
                    "payload engine"
                )

        return errors
