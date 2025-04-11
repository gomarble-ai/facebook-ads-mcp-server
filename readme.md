# Facebook Ads MCP Server

This project provides an MCP (Marble Control Plane) server acting as an interface to the Facebook Ads, enabling programmatic access to Facebook Ads data and management features.

## Prerequisites

*   Python 3.10+
*   Dependencies listed in `requirements.txt`

## Setup

1.  **(Optional but Recommended) Create and Activate a Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

    Using a virtual environment helps manage project dependencies cleanly[[Source]](https://docs.python.org/3/tutorial/venv.html).
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Obtain Facebook Access Token:** Secure a Facebook User Access Token with the necessary permissions (e.g., `ads_read`). You can generate this through the Facebook Developer portal. Follow [this link](https://elfsight.com/blog/how-to-get-facebook-access-token/).

## Running the Server

Execute `server.py`, providing the access token via the `--fb-token` argument. The server will start and listen for MCP JSON-RPC requests via standard input and send responses via standard output.

```bash
python server.py --fb-token YOUR_FACEBOOK_ACCESS_TOKEN
```

## Usage with MCP Clients (e.g., Cursor, Claude Desktop)

To integrate this server with an MCP-compatible client, add a configuration similar to the following. Replace `YOUR_FACEBOOK_ACCESS_TOKEN` with your actual token and adjust the path to `server.py` if necessary.

```json
{
  "mcpServers": {
    "fb-ads-mcp-server": {
      "command": "python",
      "args": [
        "/path/to/your/fb-ads-mcp-server/server.py",
        "--fb-token",
        "YOUR_FACEBOOK_ACCESS_TOKEN"
      ]
      // If using a virtual environment, you might need to specify the python executable within the venv:
      // "command": "/path/to/your/fb-ads-mcp-server/venv/bin/python",
      // "args": [
      //   "/path/to/your/fb-ads-mcp-server/server.py",
      //   "--fb-token",
      //   "YOUR_FACEBOOK_ACCESS_TOKEN"
      // ]
    }
  }
}
```
*(Note: On Windows, you might need to adjust the command structure or use `cmd /k` depending on your setup.)*

## Available MCP Tools

This MCP server provides tools for interacting with Facebook Ads objects and data:

| Tool Name                       | Description                                              |
| ------------------------------- | -------------------------------------------------------- |
| **Account & Object Read**       |                                                          |
| `list_ad_accounts`              | Lists ad accounts linked to the token.                   |
| `get_details_of_ad_account`     | Retrieves details for a specific ad account.             |
| `get_campaign_by_id`            | Retrieves details for a specific campaign.               |
| `get_adset_by_id`               | Retrieves details for a specific ad set.                 |
| `get_ad_by_id`                  | Retrieves details for a specific ad.                     |
| `get_ad_creative_by_id`         | Retrieves details for a specific ad creative.            |
| `get_adsets_by_ids`             | Retrieves details for multiple ad sets by their IDs.     |
| **Fetching Collections**        |                                                          |
| `get_campaigns_by_adaccount`    | Retrieves campaigns within an ad account.                |
| `get_adsets_by_adaccount`       | Retrieves ad sets within an ad account.                  |
| `get_ads_by_adaccount`          | Retrieves ads within an ad account.                      |
| `get_adsets_by_campaign`        | Retrieves ad sets within a campaign.                     |
| `get_ads_by_campaign`           | Retrieves ads within a campaign.                         |
| `get_ads_by_adset`              | Retrieves ads within an ad set.                          |
| `get_ad_creatives_by_ad_id`     | Retrieves creatives associated with an ad.               |
| **Insights & Performance Data** |                                                          |
| `get_adaccount_insights`        | Retrieves performance insights for an ad account.        |
| `get_campaign_insights`         | Retrieves performance insights for a campaign.           |
| `get_adset_insights`            | Retrieves performance insights for an ad set.            |
| `get_ad_insights`               | Retrieves performance insights for an ad.                |
| `fetch_pagination_url`          | Fetches data from a pagination URL (e.g., from insights).|
| **Activity/Change History**     |                                                          |
| `get_activities_by_adaccount`   | Retrieves change history for an ad account.              |
| `get_activities_by_adset`       | Retrieves change history for an ad set.                  |

*(Note: Most tools support additional parameters like `fields`, `filtering`, `limit`, pagination, date ranges, etc. Refer to the detailed docstrings within `server.py` for the full list and description of arguments for each tool.)*

## Dependencies

*   [mcp](https://pypi.org/project/mcp/) (>=1.6.0)
*   [requests](https://pypi.org/project/requests/) (>=2.32.3)

## License
This project is licensed under the MIT License.
