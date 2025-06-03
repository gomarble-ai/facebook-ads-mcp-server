# Facebook Ads MCP Server

[![smithery badge](https://smithery.ai/badge/@gomarble-ai/facebook-ads-mcp-server)](https://smithery.ai/server/@gomarble-ai/facebook-ads-mcp-server)

This project provides an MCP server acting as an interface to the Facebook Ads, enabling programmatic access to Facebook Ads data and management features.

<video controls width="1920" height="512" src="https://github.com/user-attachments/assets/c4a76dcf-cf5d-4a1d-b976-08165e880fe4">Your browser does not support the video tag.</video>

## Easy One-Click Setup

For a simpler setup experience, we offer ready-to-use installers:

*   **⊞ Windows:** 👉 [Download gomarble_mcp_tools.exe](https://raw.githubusercontent.com/gomarble-ai/facebook-ads-mcp-server/main/installer/win/gomarble_mcp_tools.exe)
*   ** MacOS:** 👉 [Download gomarble_mcp_tools.pkg](https://raw.githubusercontent.com/gomarble-ai/facebook-ads-mcp-server/main/installer/macos/gomarble_mcp_tools.pkg)

### What It Does

- Installs and configures the MCP server locally
- Automatically handles environment setup
- Prompts for Facebook token authentication during the process which is optional
- If facebook access token is not provided then connect to GoMarble's server to create the token on your behalf

### Important Disclaimer

This setup **does not require** you to manually obtain a Facebook Developer Access Token.

Instead, it connects securely to **GoMarble's server to create the token on your behalf**.
GoMarble **does not store** your token — it is saved locally on your machine for use with the MCP server.

---

## Setup

### Prerequisites

*   Node.js v16+ (automatically installed by the installers if not present)
*   Dependencies will be installed automatically by the installer

1.  **Install Dependencies (if setting up manually):**
    ```bash
    npm install auth-mcp-tools
    ```

2.  **Obtain API Key:** The installer will automatically obtain an API key during setup, or you can obtain one from the GoMarble platform.

### Usage with MCP Clients (e.g., Cursor, Claude Desktop)

The installer automatically configures Claude Desktop with the appropriate MCP servers. If you need to manually configure it, add the following to your Claude Desktop configuration file (typically at `$APPDATA/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "auth-mcp-tools": {
      "command": "node",
      "args": [
        "/path/to/your/install/directory/build/index.js"
      ]
    },
    "ads-mcp-server": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://mcp.gomarble.ai/sse",
        "--header",
        "Authorization: ${AUTH_HEADER}"
      ],
      "env": {
        "AUTH_HEADER": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

Replace `YOUR_API_KEY` with your actual API key and adjust the path to `index.js` if necessary.

Restart the MCP Client app after making the update in the configuration.

### Debugging the Server

If you need to run the server directly:

```bash
node /path/to/your/install/directory/build/index.js
```

For the remote MCP server:

```bash
npx mcp-remote https://mcp.gomarble.ai/sse --header "Authorization: Bearer YOUR_API_KEY"
```

### Available MCP Tools

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

*(Note: Most tools support additional parameters like `fields`, `filtering`, `limit`, pagination, date ranges, etc. Refer to the detailed documentation in the tool descriptions.)*

*(Note: If your API key expires, you may need to generate a new one and update the configuration file of the MCP Client.)*

### Dependencies

*   Node.js v16+
*   [auth-mcp-tools](https://www.npmjs.com/package/auth-mcp-tools)
*   [mcp-remote](https://www.npmjs.com/package/mcp-remote) (for remote server connectivity)

### License
This project is licensed under the MIT License.

---

## Installing via Smithery

To install Facebook Ads Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@gomarble-ai/facebook-ads-mcp-server):

```bash
npx -y @smithery/cli install @gomarble-ai/facebook-ads-mcp-server --client claude
```
