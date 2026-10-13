READINESS_STATES = {
    "runtime-tested": {
        "label": "✓ READY",
        "buildable": True,
        "tone": "success",
    },
    "build-tested": {
        "label": "BUILD OK",
        "buildable": True,
        "tone": "info",
    },
    "planned": {
        "label": "PLANNED",
        "buildable": False,
        "tone": "warning",
    },
}


def validation_status(
    method
):
    operational = method.get(
        "operational",
        {}
    )

    if not isinstance(
        operational,
        dict
    ):
        return "unknown"

    return operational.get(
        "validation",
        "unknown"
    )


def readiness_for(
    method
):
    validation = validation_status(
        method
    )

    state = READINESS_STATES.get(
        validation
    )

    if state is None:
        return {
            "validation": validation,
            "label": "UNKNOWN",
            "buildable": False,
            "tone": "warning",
        }

    return {
        "validation": validation,
        **state,
    }


def is_buildable(
    method
):
    return readiness_for(
        method
    )["buildable"]
