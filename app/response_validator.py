REQUIRED_FIELDS = {
    "body",
    "cta",
    "send_as",
    "rationale",
}


class ResponseValidator:

    def validate(self, response):

        if not isinstance(response, dict):
            raise ValueError(
                "LLM response must be an object."
            )

        missing = REQUIRED_FIELDS - set(
            response.keys()
        )

        if missing:
            raise ValueError(
                f"Missing fields: {missing}"
            )

        if not isinstance(
            response["body"],
            str,
        ):
            raise ValueError(
                "body must be a string."
            )

        if response["cta"] is not None and not isinstance(
            response["cta"],
            str,
        ):
            raise ValueError(
                "cta must be string or null."
            )

        if not isinstance(
            response["send_as"],
            str,
        ):
            raise ValueError(
                "send_as must be a string."
            )

        return True