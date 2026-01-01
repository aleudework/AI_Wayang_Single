from ai_wayang_single.config.settings import WAYANG_CONFIG
import requests

class WayangExecutor:
    """
    Executes a JSON Wayang Plan in Wayang server (JSON API) and returns output

    """

    def __init__(self, url: str | None = None):
        self.url = url or WAYANG_CONFIG.get("server_url")

    def execute_plan(self, plan: str):
        """
        Execute a JSON Wayang plan and returns output
        Also returns the error stack if the server supports it

        Args: 
            plan (str): Wayang JSON plan to be executed

        Returns:
            Output from Wayang

        """

        try:
            # Send plan to Wayang server
            response = requests.post(url=self.url, json=plan)

            # Return status code and body/output/result from Wayang server
            return response.status_code, response.text

        # Handle request exceptions
        except requests.exceptions.RequestException as e:
            raise Exception(e)
    