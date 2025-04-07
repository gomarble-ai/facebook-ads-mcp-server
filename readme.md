# Facebook API MCP Server

This project provides an MCP server that acts as an interface to the Facebook Graph API, specifically for managing and retrieving insights from Facebook Ads accounts.

## Prerequisites

*   Python 3.x
*   Dependencies listed in `requirements.txt`

## Installation

1.  Clone the repository (if applicable).
2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Setup

1.  **Facebook Access Token:** This server requires a Facebook User Access Token with the necessary permissions (e.g., `ads_read`, `ads_management`, `business_management`).
2.  **Authentication:**
    *   The server includes a tool (`refresh_facebook_token`) to help obtain and refresh the token using an external authentication helper service (`https://reimagine.gomarble.ai`).
    *   When you run the `refresh_facebook_token` tool for the first time (or when the token expires), it will open a browser window for you to log in to Facebook and grant permissions.
    *   Upon successful authentication, the tool will fetch the access token from the auth helper service and save it locally in a file named `fb_token` in the same directory as `server.py`.
    *   Subsequent API calls will automatically use the token from the `fb_token` file.

## Running the Server

Execute the `server.py` script:

```bash
python server.py
```

The server will start and listen for MCP requests (defaulting to stdio transport).

## Available MCP Tools

The server exposes the following tools via the MCP interface:

*   **`list_ad_accounts()`**: Lists ad accounts associated with the authenticated Facebook user.
*   **`get_details_of_ad_account(act_id: str, fields: list[str] = None)`**: Retrieves details for a specific ad account (`act_id`). Optionally specify which `fields` to return.
*   **`get_adaccount_insights(...)`**: Gets performance insights for a specific ad account (`act_id`). Supports various parameters for time range, level, breakdowns, filtering, etc.
*   **`get_campaign_insights(...)`**: Gets performance insights for a specific ad campaign (`campaign_id`). Supports various parameters.
*   **`get_adset_insights(...)`**: Gets performance insights for a specific ad set (`adset_id`). Supports various parameters.
*   **`get_ad_insights(...)`**: Gets performance insights for a specific ad (`ad_id`). Supports various parameters.
*   **`fetch_pagination_url(url: str)`**: Fetches the next or previous page of results from an insights API call using the provided pagination `url`.
*   **`refresh_facebook_token(scope: str = ...)`**: Initiates the process to obtain/refresh the Facebook access token using the secure auth server flow. Opens a browser for user authentication.

*(Refer to the docstrings within `server.py` for detailed argument descriptions for each insights tool.)*

## Dependencies

*   [mcp](https://pypi.org/project/mcp/) (>=1.6.0)
*   [requests](https://pypi.org/project/requests/) (>=2.32.3)

## Notes

*   The server communicates with `https://graph.facebook.com/v22.0`.
*   Token refresh relies on the external service at `https://reimagine.gomarble.ai`.
*   Ensure the `fb_token` file is kept secure and is not committed to version control if it contains sensitive access tokens. Consider adding `fb_token` to your `.gitignore` file.
