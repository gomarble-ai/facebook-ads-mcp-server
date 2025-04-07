# server.py
from mcp.server.fastmcp import FastMCP
import requests
from typing import Dict, List, Optional, Any
import json
import os
import webbrowser
import time
import uuid
import requests
    

# --- Constants ---
FB_API_VERSION = "v22.0"
FB_GRAPH_URL = f"https://graph.facebook.com/{FB_API_VERSION}"
AUTH_SERVER_BASE_URL = "https://reimagine.gomarble.ai"
DEFAULT_AD_ACCOUNT_FIELDS = [
    'name', 'business_name', 'age', 'account_status', 'balance',
    'amount_spent', 'attribution_spec', 'account_id', 'business',
    'business_city', 'brand_safety_content_filter_levels', 'currency',
    'created_time', 'id'
]

# Create an MCP server
mcp = FastMCP("fb-api-mcp-server")

# Add a global variable to store the token
FB_ACCESS_TOKEN = None

# --- Helper Functions ---

def _get_fb_access_token() -> str:
    """Get Facebook access token, reading from file only once."""
    global FB_ACCESS_TOKEN
    if FB_ACCESS_TOKEN is None:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            token_path = os.path.join(current_dir, 'fb_token')
            with open(token_path, 'r') as file:
                FB_ACCESS_TOKEN = file.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError("Facebook token file 'fb_token' not found")
        except Exception as e:
            raise Exception(f"Error reading Facebook token: {str(e)}")
    return FB_ACCESS_TOKEN

def _make_graph_api_call(url: str, params: Dict[str, Any]) -> Dict:
    """Makes a GET request to the Facebook Graph API and handles the response."""
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def _build_insights_params(
    params: Dict[str, Any],
    fields: Optional[List[str]] = None,
    date_preset: Optional[str] = None,
    time_range: Optional[Dict[str, str]] = None,
    time_ranges: Optional[List[Dict[str, str]]] = None,
    time_increment: Optional[str] = None,
    level: Optional[str] = None,
    action_attribution_windows: Optional[List[str]] = None,
    action_breakdowns: Optional[List[str]] = None,
    action_report_time: Optional[str] = None,
    breakdowns: Optional[List[str]] = None,
    default_summary: bool = False,
    use_account_attribution_setting: bool = False,
    use_unified_attribution_setting: bool = True,
    filtering: Optional[List[dict]] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    offset: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    locale: Optional[str] = None
) -> Dict[str, Any]:
    """Builds the common parameter dictionary for insights API calls."""
    if fields:
        params['fields'] = ','.join(fields)
    
    # Time parameters
    time_params_provided = time_range or time_ranges or since or until
    if not time_params_provided and date_preset:
        params['date_preset'] = date_preset
    if time_range:
        params['time_range'] = json.dumps(time_range)
    if time_ranges:
        params['time_ranges'] = json.dumps(time_ranges)
    if time_increment and time_increment != 'all_days':
        params['time_increment'] = time_increment
    # Time-based pagination (only if specific time range isn't set)
    if not time_range and not time_ranges:
        if since:
            params['since'] = since
        if until:
            params['until'] = until

    if level:
        params['level'] = level

    # Action parameters
    if action_attribution_windows:
        params['action_attribution_windows'] = ','.join(action_attribution_windows)
    if action_breakdowns:
        params['action_breakdowns'] = ','.join(action_breakdowns)
    if action_report_time:
        params['action_report_time'] = action_report_time
    
    # Breakdown parameters
    if breakdowns:
        params['breakdowns'] = ','.join(breakdowns)
    
    # Summary and attribution settings
    if default_summary:
        params['default_summary'] = 'true'
    if use_account_attribution_setting:
        params['use_account_attribution_setting'] = 'true'
    # Only add unified if True (it defaults to False in API if omitted)
    if use_unified_attribution_setting:
        params['use_unified_attribution_setting'] = 'true'
    
    # Filtering, Sorting, Limit
    if filtering:
        # Ensure filtering is passed as a JSON string if it's complex
        params['filtering'] = json.dumps(filtering) if isinstance(filtering, (list, dict)) else filtering
    if sort:
        params['sort'] = sort
    if limit is not None: # Check for None explicitly as limit can be 0
        params['limit'] = limit
        
    # Pagination parameters
    if after:
        params['after'] = after
    if before:
        params['before'] = before
    if offset is not None:
        params['offset'] = offset
        
    # Add locale if provided
    if locale:
        params['locale'] = locale
        
    return params


# --- MCP Tools ---

@mcp.tool()
def list_ad_accounts() -> Dict:
    """List down the ad accounts and their names associated with your Facebook account"""
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/me"
    params = {
        'access_token': access_token,
        'fields': 'adaccounts{name}'
    }
    return _make_graph_api_call(url, params)


@mcp.tool()
def get_details_of_ad_account(act_id: str, fields: list[str] = None) -> Dict:
    """Get details of a specific ad account as per the fields provided
    Args:
        act_id: The act ID of the ad account, example: act_1234567890
        fields: The fields to get from the ad account. If None, defaults are used.
                Available fields include: name, business_name, age, account_status,
                balance, amount_spent, attribution_spec, account_id, business,
                business_city, brand_safety_content_filter_levels, currency,
                created_time, id.
    Returns:    
        A dictionary containing the details of the ad account
    """
    if fields is None:
        fields = DEFAULT_AD_ACCOUNT_FIELDS
    
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}"
    params = {
        'access_token': access_token,
        'fields': ','.join(fields)
    }
    return _make_graph_api_call(url, params)


@mcp.tool()
def get_adaccount_insights(
    act_id: str,
    fields: Optional[List[str]] = None,
    date_preset: str = 'last_30d',
    time_range: Optional[Dict[str, str]] = None,
    time_ranges: Optional[List[Dict[str, str]]] = None,
    time_increment: str = 'all_days',
    level: str = 'account',
    action_attribution_windows: Optional[List[str]] = None,
    action_breakdowns: Optional[List[str]] = None,
    action_report_time: Optional[str] = None,
    breakdowns: Optional[List[str]] = None,
    default_summary: bool = False,
    use_account_attribution_setting: bool = False,
    use_unified_attribution_setting: bool = True,
    filtering: Optional[List[dict]] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    offset: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    locale: Optional[str] = None
) -> Dict:
    """Retrieves performance insights for a specified Facebook ad account.

    This tool interfaces with the Facebook Graph API's Insights edge to fetch comprehensive
    performance data, such as impressions, reach, cost, conversions, and more. It supports
    various options for filtering, time breakdowns, and attribution settings. Note that
    some metrics returned might be estimated or in development.

    Args:
        act_id (str): The target ad account ID, prefixed with 'act_', e.g., 'act_1234567890'.
        fields (Optional[List[str]]): A list of specific metrics and fields to retrieve.
            If omitted, a default set is returned by the API. Common examples include:
                - 'account_currency', 'account_id', 'account_name'
                - 'actions', 'clicks', 'conversions'
                - 'cpc', 'cpm', 'cpp', 'ctr'
                - 'frequency', 'impressions', 'reach', 'spend'.
        date_preset (str): A predefined relative time range for the report.
            Options: 'today', 'yesterday', 'this_month', 'last_month', 'this_quarter',
            'maximum', 'last_3d', 'last_7d', 'last_14d', 'last_28d', 'last_30d',
            'last_90d', 'last_week_mon_sun', 'last_week_sun_sat', 'last_quarter',
            'last_year', 'this_week_mon_today', 'this_week_sun_today', 'this_year'.
            Default: 'last_30d'. This parameter is ignored if 'time_range', 'time_ranges',
            'since', or 'until' is provided.
        time_range (Optional[Dict[str, str]]): A specific time range defined by 'since' and 'until'
            dates in 'YYYY-MM-DD' format, e.g., {'since': '2023-10-01', 'until': '2023-10-31'}.
            Overrides 'date_preset'. Ignored if 'time_ranges' is provided.
        time_ranges (Optional[List[Dict[str, str]]]): An array of time range objects
            ({'since': '...', 'until': '...'}) for comparing multiple periods. Overrides
            'time_range' and 'date_preset'. Time ranges can overlap.
        time_increment (str | int): Specifies the granularity of the time breakdown.
            - An integer from 1 to 90 indicates the number of days per data point.
            - 'monthly': Aggregates data by month.
            - 'all_days': Provides a single summary row for the entire period.
            Default: 'all_days'.
        level (str): The level of aggregation for the insights.
            Options: 'account', 'campaign', 'adset', 'ad'.
            Default: 'account'.
        action_attribution_windows (Optional[List[str]]): Specifies the attribution windows
            to consider for actions (conversions). Examples: '1d_view', '7d_view',
            '28d_view', '1d_click', '7d_click', '28d_click', 'dda', 'default'.
            The API default may vary; ['7d_click', '1d_view'] is common.
        action_breakdowns (Optional[List[str]]): Segments the 'actions' results based on
            specific dimensions. Examples: 'action_device', 'action_type',
            'conversion_destination', 'action_destination'. Default: ['action_type'].
        action_report_time (Optional[str]): Determines when actions are counted.
            - 'impression': Actions are attributed to the time of the ad impression.
            - 'conversion': Actions are attributed to the time the conversion occurred.
            - 'mixed': Uses 'impression' time for paid metrics, 'conversion' time for organic.
            Default: 'mixed'.
        breakdowns (Optional[List[str]]): Segments the results by dimensions like demographics
            or placement. Examples: 'age', 'gender', 'country', 'region', 'dma',
            'impression_device', 'publisher_platform', 'platform_position', 'device_platform'.
            Note: Not all breakdowns can be combined.
        default_summary (bool): If True, includes an additional summary row in the response.
            Default: False.
        use_account_attribution_setting (bool): If True, forces the report to use the
            attribution settings defined at the ad account level. Default: False.
        use_unified_attribution_setting (bool): If True, uses the unified attribution
            settings defined at the ad set level. This is generally recommended for
            consistency with Ads Manager reporting. Default: True.
        filtering (Optional[List[dict]]): A list of filter objects to apply to the data.
            Each object should have 'field', 'operator', and 'value' keys.
            Example: [{'field': 'spend', 'operator': 'GREATER_THAN', 'value': 50}].
        sort (Optional[str]): Specifies the field and direction for sorting the results.
            Format: '{field_name}_ascending' or '{field_name}_descending'.
            Example: 'impressions_descending'.
        limit (Optional[int]): The maximum number of results to return in one API response page.
        after (Optional[str]): A pagination cursor pointing to the next page of results.
            Obtained from the 'paging.cursors.after' field of a previous response.
        before (Optional[str]): A pagination cursor pointing to the previous page of results.
            Obtained from the 'paging.cursors.before' field of a previous response.
        offset (Optional[int]): An alternative pagination method; skips the specified
            number of results. Use cursor-based pagination ('after'/'before') when possible.
        since (Optional[str]): For time-based pagination (used if 'time_range' and 'time_ranges'
            are not set), the start timestamp (Unix or strtotime value).
        until (Optional[str]): For time-based pagination (used if 'time_range' and 'time_ranges'
            are not set), the end timestamp (Unix or strtotime value).
        locale (Optional[str]): The locale for text responses (e.g., 'en_US'). This controls 
            language and formatting of text fields in the response.

    Returns:
        Dict: A dictionary containing the requested ad account insights. The main results
              are in the 'data' list, and pagination info is in the 'paging' object.

    Example:
        ```python
        # Get basic ad account performance for the last 30 days
        insights = get_adaccount_insights(
            act_id="act_123456789",
            fields=["impressions", "clicks", "spend", "ctr"],
            limit=25
        )

        # Fetch the next page if available using the pagination tool
        next_page_url = insights.get("paging", {}).get("next")
        if next_page_url:
            next_page_results = fetch_pagination_url(url=next_page_url)
            print("Fetched next page results.")
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/insights"
    params = {'access_token': access_token}

    params = _build_insights_params(
        params=params,
        fields=fields,
        date_preset=date_preset,
        time_range=time_range,
        time_ranges=time_ranges,
        time_increment=time_increment,
        level=level,
        action_attribution_windows=action_attribution_windows,
        action_breakdowns=action_breakdowns,
        action_report_time=action_report_time,
        breakdowns=breakdowns,
        default_summary=default_summary,
        use_account_attribution_setting=use_account_attribution_setting,
        use_unified_attribution_setting=use_unified_attribution_setting,
        filtering=filtering,
        sort=sort,
        limit=limit,
        after=after,
        before=before,
        offset=offset,
        since=since,
        until=until,
        locale=locale
    )

    return _make_graph_api_call(url, params)

@mcp.tool()
def get_campaign_insights(
    campaign_id: str,
    fields: Optional[List[str]] = None,
    date_preset: str = 'last_30d',
    time_range: Optional[Dict[str, str]] = None,
    time_ranges: Optional[List[Dict[str, str]]] = None,
    time_increment: str = 'all_days',
    action_attribution_windows: Optional[List[str]] = None,
    action_breakdowns: Optional[List[str]] = None,
    action_report_time: Optional[str] = None,
    breakdowns: Optional[List[str]] = None,
    default_summary: bool = False,
    use_account_attribution_setting: bool = False,
    use_unified_attribution_setting: bool = True,
    level: Optional[str] = None,
    filtering: Optional[List[dict]] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    offset: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    locale: Optional[str] = None
) -> Dict:
    """Retrieves performance insights for a specific Facebook ad campaign.

    Fetches statistics for a given campaign ID, allowing analysis of metrics like
    impressions, clicks, conversions, spend, etc. Supports time range definitions,
    breakdowns, and attribution settings.

    Args:
        campaign_id (str): The ID of the target Facebook ad campaign, e.g., '23843xxxxx'.
        fields (Optional[List[str]]): A list of specific metrics and fields to retrieve.
            Common examples: 'campaign_name', 'account_id', 'impressions', 'clicks',
            'spend', 'ctr', 'reach', 'actions', 'objective', 'cost_per_action_type',
            'conversions', 'cpc', 'cpm', 'cpp', 'frequency', 'date_start', 'date_stop'.
        date_preset (str): A predefined relative time range for the report.
            Options: 'today', 'yesterday', 'this_month', 'last_month', 'this_quarter',
            'maximum', 'last_3d', 'last_7d', 'last_14d', 'last_28d', 'last_30d',
            'last_90d', 'last_week_mon_sun', 'last_week_sun_sat', 'last_quarter',
            'last_year', 'this_week_mon_today', 'this_week_sun_today', 'this_year'.
            Default: 'last_30d'. Ignored if 'time_range', 'time_ranges', 'since', or 'until' is used.
        time_range (Optional[Dict[str, str]]): A specific time range {'since':'YYYY-MM-DD','until':'YYYY-MM-DD'}.
            Overrides 'date_preset'. Ignored if 'time_ranges' is provided.
        time_ranges (Optional[List[Dict[str, str]]]): An array of time range objects for comparison.
            Overrides 'time_range' and 'date_preset'.
        time_increment (str | int): Specifies the granularity of the time breakdown.
            - Integer (1-90): number of days per data point.
            - 'monthly': Aggregates data by month.
            - 'all_days': Single summary row for the period.
            Default: 'all_days'.
        action_attribution_windows (Optional[List[str]]): Specifies attribution windows for actions.
            Examples: '1d_view', '7d_click', '28d_click', etc. Default depends on API/settings.
        action_breakdowns (Optional[List[str]]): Segments 'actions' results. Examples: 'action_device', 'action_type'.
            Default: ['action_type'].
        action_report_time (Optional[str]): Determines when actions are counted ('impression', 'conversion', 'mixed').
            Default: 'mixed'.
        breakdowns (Optional[List[str]]): Segments results by dimensions. Examples: 'age', 'gender', 'country',
            'publisher_platform', 'impression_device'.
        default_summary (bool): If True, includes an additional summary row. Default: False.
        use_account_attribution_setting (bool): If True, uses the ad account's attribution settings. Default: False.
        use_unified_attribution_setting (bool): If True, uses unified attribution settings. Default: True.
        level (Optional[str]): Level of aggregation ('campaign', 'adset', 'ad'). Default: 'campaign'.
        filtering (Optional[List[dict]]): List of filter objects {'field': '...', 'operator': '...', 'value': '...'}.
        sort (Optional[str]): Field and direction for sorting ('{field}_ascending'/'_descending').
        limit (Optional[int]): Maximum number of results per page.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        offset (Optional[int]): Alternative pagination: skips N results.
        since (Optional[str]): Start timestamp for time-based pagination (if time ranges absent).
        until (Optional[str]): End timestamp for time-based pagination (if time ranges absent).
        locale (Optional[str]): The locale for text responses (e.g., 'en_US'). This controls 
            language and formatting of text fields in the response.

    Returns:
        Dict: A dictionary containing the requested campaign insights, with 'data' and 'paging' keys.

    Example:
        ```python
        # Get basic campaign performance for the last 7 days
        insights = get_campaign_insights(
            campaign_id="23843xxxxx",
            fields=["campaign_name", "impressions", "clicks", "spend"],
            date_preset="last_7d",
            limit=50
        )

        # Fetch the next page if available
        next_page_url = insights.get("paging", {}).get("next")
        if next_page_url:
            next_page_results = fetch_pagination_url(url=next_page_url)
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{campaign_id}/insights"
    params = {'access_token': access_token}

    # Default level to 'campaign' if not provided for this specific tool
    effective_level = level if level else 'campaign'

    params = _build_insights_params(
        params=params,
        fields=fields,
        date_preset=date_preset,
        time_range=time_range,
        time_ranges=time_ranges,
        time_increment=time_increment,
        level=effective_level,
        action_attribution_windows=action_attribution_windows,
        action_breakdowns=action_breakdowns,
        action_report_time=action_report_time,
        breakdowns=breakdowns,
        default_summary=default_summary,
        use_account_attribution_setting=use_account_attribution_setting,
        use_unified_attribution_setting=use_unified_attribution_setting,
        filtering=filtering,
        sort=sort,
        limit=limit,
        after=after,
        before=before,
        offset=offset,
        since=since,
        until=until,
        locale=locale
    )
    return _make_graph_api_call(url, params)

@mcp.tool()
def get_adset_insights(
    adset_id: str,
    fields: Optional[List[str]] = None,
    date_preset: str = 'last_30d',
    time_range: Optional[Dict[str, str]] = None,
    time_ranges: Optional[List[Dict[str, str]]] = None,
    time_increment: str = 'all_days',
    action_attribution_windows: Optional[List[str]] = None,
    action_breakdowns: Optional[List[str]] = None,
    action_report_time: Optional[str] = None,
    breakdowns: Optional[List[str]] = None,
    default_summary: bool = False,
    use_account_attribution_setting: bool = False,
    use_unified_attribution_setting: bool = True,
    level: Optional[str] = None,
    filtering: Optional[List[dict]] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    offset: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    locale: Optional[str] = None
) -> Dict:
    """Retrieves performance insights for a specific Facebook ad set.

    Provides advertising performance statistics for an ad set, allowing for analysis
    of metrics across its child ads. Supports time range definitions, breakdowns,
    filtering, sorting, and attribution settings. Some metrics may be estimated
    or in development.
    
    Args:
        adset_id (str): The ID of the target ad set, e.g., '6123456789012'.
        fields (Optional[List[str]]): A list of specific metrics and fields. Common examples:
            'adset_name', 'campaign_name', 'account_id', 'impressions', 'clicks', 'spend',
            'ctr', 'reach', 'frequency', 'actions', 'conversions', 'cpc', 'cpm', 'cpp',
            'cost_per_action_type', 'video_p25_watched_actions', 'website_purchases'.
        date_preset (str): A predefined relative time range ('last_30d', 'last_7d', etc.).
            Default: 'last_30d'. Ignored if 'time_range', 'time_ranges', 'since', or 'until' is used.
        time_range (Optional[Dict[str, str]]): Specific time range {'since':'YYYY-MM-DD','until':'YYYY-MM-DD'}.
            Overrides 'date_preset'. Ignored if 'time_ranges' is provided.
        time_ranges (Optional[List[Dict[str, str]]]): Array of time range objects for comparison.
            Overrides 'time_range' and 'date_preset'.
        time_increment (str | int): Granularity of the time breakdown ('all_days', 'monthly', 1-90 days).
            Default: 'all_days'.
        action_attribution_windows (Optional[List[str]]): Specifies attribution windows for actions.
            Examples: '1d_view', '7d_click'. Default depends on API/settings.
        action_breakdowns (Optional[List[str]]): Segments 'actions' results. Examples: 'action_device', 'action_type'.
            Default: ['action_type'].
        action_report_time (Optional[str]): Time basis for action stats ('impression', 'conversion', 'mixed').
            Default: 'mixed'.
        breakdowns (Optional[List[str]]): Segments results by dimensions. Examples: 'age', 'gender', 'country',
            'publisher_platform', 'impression_device', 'platform_position'.
        default_summary (bool): If True, includes an additional summary row. Default: False.
        use_account_attribution_setting (bool): If True, uses the ad account's attribution settings. Default: False.
        use_unified_attribution_setting (bool): If True, uses unified attribution settings. Default: True.
        level (Optional[str]): Level of aggregation ('adset', 'ad'). Default: 'adset'.
        filtering (Optional[List[dict]]): List of filter objects {'field': '...', 'operator': '...', 'value': '...'}.
        sort (Optional[str]): Field and direction for sorting ('{field}_ascending'/'_descending').
        limit (Optional[int]): Maximum number of results per page.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        offset (Optional[int]): Alternative pagination: skips N results.
        since (Optional[str]): Start timestamp for time-based pagination (if time ranges absent).
        until (Optional[str]): End timestamp for time-based pagination (if time ranges absent).
        locale (Optional[str]): The locale for text responses (e.g., 'en_US'). This controls 
            language and formatting of text fields in the response.
    
    Returns:    
        Dict: A dictionary containing the requested ad set insights, with 'data' and 'paging' keys.

    Example:
        ```python
        # Get ad set performance with breakdown by device for last 14 days
        insights = get_adset_insights(
            adset_id="6123456789012",
            fields=["adset_name", "impressions", "spend"],
            breakdowns=["impression_device"],
            date_preset="last_14d"
        )

        # Fetch the next page if available
        next_page_url = insights.get("paging", {}).get("next")
        if next_page_url:
            next_page_results = fetch_pagination_url(url=next_page_url)
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{adset_id}/insights"
    params = {'access_token': access_token}

    # Default level to 'adset' if not provided for this specific tool
    effective_level = level if level else 'adset'

    params = _build_insights_params(
        params=params,
        fields=fields,
        date_preset=date_preset,
        time_range=time_range,
        time_ranges=time_ranges,
        time_increment=time_increment,
        level=effective_level,
        action_attribution_windows=action_attribution_windows,
        action_breakdowns=action_breakdowns,
        action_report_time=action_report_time,
        breakdowns=breakdowns,
        default_summary=default_summary,
        use_account_attribution_setting=use_account_attribution_setting,
        use_unified_attribution_setting=use_unified_attribution_setting,
        filtering=filtering,
        sort=sort,
        limit=limit,
        after=after,
        before=before,
        offset=offset,
        since=since,
        until=until,
        locale=locale
    )

    return _make_graph_api_call(url, params)


@mcp.tool()
def get_ad_insights(
    ad_id: str,
    fields: Optional[List[str]] = None,
    date_preset: str = 'last_30d',
    time_range: Optional[Dict[str, str]] = None,
    time_ranges: Optional[List[Dict[str, str]]] = None,
    time_increment: str = 'all_days',
    action_attribution_windows: Optional[List[str]] = None,
    action_breakdowns: Optional[List[str]] = None,
    action_report_time: Optional[str] = None,
    breakdowns: Optional[List[str]] = None,
    default_summary: bool = False,
    use_account_attribution_setting: bool = False,
    use_unified_attribution_setting: bool = True,
    level: Optional[str] = None,
    filtering: Optional[List[dict]] = None,
    sort: Optional[str] = None,
    limit: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    offset: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    locale: Optional[str] = None
) -> Dict:  
    """Retrieves detailed performance insights for a specific Facebook ad.

    Fetches performance metrics for an individual ad (ad group), such as impressions,
    clicks, conversions, engagement, video views, etc. Allows for customization via
    time periods, breakdowns, filtering, sorting, and attribution settings. Note that
    some metrics may be estimated or in development.
    
    Args:
        ad_id (str): The ID of the target ad (ad group), e.g., '6123456789012'.
        fields (Optional[List[str]]): A list of specific metrics and fields. Common examples:
            'ad_name', 'adset_name', 'campaign_name', 'account_id', 'impressions', 'clicks',
            'spend', 'ctr', 'cpc', 'cpm', 'cpp', 'reach', 'frequency', 'actions', 'conversions',
            'cost_per_action_type', 'inline_link_clicks', 'inline_post_engagement', 'unique_clicks',
            'video_p25_watched_actions', 'video_p50_watched_actions', 'video_p75_watched_actions',
            'video_p95_watched_actions', 'video_p100_watched_actions', 'video_avg_time_watched_actions',
            'website_ctr', 'website_purchases'.
        date_preset (str): A predefined relative time range ('last_30d', 'last_7d', etc.).
            Default: 'last_30d'. Ignored if 'time_range', 'time_ranges', 'since', or 'until' is used.
        time_range (Optional[Dict[str, str]]): Specific time range {'since':'YYYY-MM-DD','until':'YYYY-MM-DD'}.
            Overrides 'date_preset'. Ignored if 'time_ranges' is provided.
        time_ranges (Optional[List[Dict[str, str]]]): Array of time range objects for comparison.
            Overrides 'time_range' and 'date_preset'.
        time_increment (str | int): Granularity of the time breakdown ('all_days', 'monthly', 1-90 days).
            Default: 'all_days'.
        action_attribution_windows (Optional[List[str]]): Specifies attribution windows for actions.
            Examples: '1d_view', '7d_click'. Default depends on API/settings.
        action_breakdowns (Optional[List[str]]): Segments 'actions' results. Examples: 'action_device', 'action_type'.
            Default: ['action_type'].
        action_report_time (Optional[str]): Time basis for action stats ('impression', 'conversion', 'mixed').
            Default: 'mixed'.
        breakdowns (Optional[List[str]]): Segments results by dimensions. Examples: 'age', 'gender', 'country',
            'publisher_platform', 'impression_device', 'platform_position', 'device_platform'.
        default_summary (bool): If True, includes an additional summary row. Default: False.
        use_account_attribution_setting (bool): If True, uses the ad account's attribution settings. Default: False.
        use_unified_attribution_setting (bool): If True, uses unified attribution settings. Default: True.
        level (Optional[str]): Level of aggregation. Should typically be 'ad'. Default: 'ad'.
        filtering (Optional[List[dict]]): List of filter objects {'field': '...', 'operator': '...', 'value': '...'}.
        sort (Optional[str]): Field and direction for sorting ('{field}_ascending'/'_descending').
        limit (Optional[int]): Maximum number of results per page.
        after (Optional[str]): Pagination cursor for the next page.
        before (Optional[str]): Pagination cursor for the previous page.
        offset (Optional[int]): Alternative pagination: skips N results.
        since (Optional[str]): Start timestamp for time-based pagination (if time ranges absent).
        until (Optional[str]): End timestamp for time-based pagination (if time ranges absent).
        locale (Optional[str]): The locale for text responses (e.g., 'en_US'). This controls 
            language and formatting of text fields in the response.
    
    Returns:    
        Dict: A dictionary containing the requested ad insights, with 'data' and 'paging' keys.
        
    Example:
        ```python
        # Get basic ad performance for the last 30 days
        ad_insights = get_ad_insights(
            ad_id="6123456789012", 
            fields=["ad_name", "impressions", "clicks", "spend", "ctr", "reach"],
            limit=10
        )
        
        # Get ad performance with platform breakdown for last 14 days
        platform_insights = get_ad_insights(
            ad_id="6123456789012",
            fields=["ad_name", "impressions", "clicks", "spend"],
            breakdowns=["publisher_platform", "platform_position"],
            date_preset="last_14d"
        )
        
        # Fetch the next page of basic performance if available
        next_page_url = ad_insights.get("paging", {}).get("next")
        if next_page_url:
            next_page = fetch_pagination_url(url=next_page_url)
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{ad_id}/insights"
    params = {'access_token': access_token}

    # Default level to 'ad' if not provided for this specific tool
    effective_level = level if level else 'ad'

    params = _build_insights_params(
        params=params,
        fields=fields,
        date_preset=date_preset,
        time_range=time_range,
        time_ranges=time_ranges,
        time_increment=time_increment,
        level=effective_level,
        action_attribution_windows=action_attribution_windows,
        action_breakdowns=action_breakdowns,
        action_report_time=action_report_time,
        breakdowns=breakdowns,
        default_summary=default_summary,
        use_account_attribution_setting=use_account_attribution_setting,
        use_unified_attribution_setting=use_unified_attribution_setting,
        filtering=filtering,
        sort=sort,
        limit=limit,
        after=after,
        before=before,
        offset=offset,
        since=since,
        until=until,
        locale=locale
    )

    return _make_graph_api_call(url, params)


@mcp.tool()
def fetch_pagination_url(url: str) -> Dict:
    """Fetch data from a Facebook Graph API pagination URL
    
    Use this to get the next/previous page of results from an insights API call.
    
    Args:
        url: The complete pagination URL (e.g., from response['paging']['next'] or response['paging']['previous']).
             It includes the necessary token and parameters.
             
    Returns:
        The dictionary containing the next/previous page of results.
        
    Example:
        ```python
        # Assuming 'initial_results' is the dict from a previous insights call
        if "paging" in initial_results and "next" in initial_results["paging"]:
            next_page_data = fetch_pagination_url(url=initial_results["paging"]["next"])

        if "paging" in initial_results and "previous" in initial_results["paging"]:
            prev_page_data = fetch_pagination_url(url=initial_results["paging"]["previous"])
        ```
    """
    # This function takes a full URL which already includes the access token,
    # so we don't use the _make_graph_api_call helper here.
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


@mcp.tool()
def refresh_facebook_token(
    scope: str = "email,ads_read,ads_management,public_profile,business_management,catalog_management"
) -> Dict:
    """Refresh the Facebook access token using the secure auth server.
    
    This tool communicates with the Facebook auth server (fb_host.py) to get a new token.
    It will open a browser window for the user to authenticate with Facebook.
    The auth server handles the token exchange securely without exposing the client credentials.
    
    Args:
        scope: Comma-separated string of permission scopes to request.
            Default is "email,ads_read,ads_management,public_profile,business_management,catalog_management".
    
    Returns:
        Dict containing status information about the token refresh process.
    """
    
    # Reset the cached token
    global FB_ACCESS_TOKEN
    FB_ACCESS_TOKEN = None
    
    # Step 1: Generate a unique request ID
    request_id = str(uuid.uuid4())
    
    # Step 2: Define the auth server URLs
    auth_start_url = f"{AUTH_SERVER_BASE_URL}/api/authorise/facebook/start?request_id={request_id}&scope={scope}"
    token_fetch_url = f"{AUTH_SERVER_BASE_URL}/api/authorise/facebook/get-token?request_id={request_id}"
    
    # Step 3: Open browser for user to authenticate with Facebook
    print(f"Opening browser for Facebook authentication...")
    webbrowser.open(auth_start_url)
    
    # Step 4: Poll the auth server for the token
    print("Waiting for authentication to complete...")
    max_attempts = 6  # 1 minute (10-second intervals)
    for attempt in range(max_attempts):
        try:
            # Wait between polls
            time.sleep(10)
            
            # Check status with the auth server
            response = requests.get(token_fetch_url, verify=False)  # Skip SSL verification for self-signed cert
            
            if response.status_code != 200:
                print(f"Error from auth server: {response.text}")
                continue
                
            data = response.json()
            
            if data["status"] == "pending":
                print(f"Authentication in progress... ({attempt+1}/{max_attempts})")
                continue
                
            if data["status"] == "error":
                return {"status": "error", "message": data.get("message", "Unknown error")}
                
            if data["status"] == "success":
                # We have the token! Save it
                access_token = data["access_token"]
                
                # Save to file
                current_dir = os.path.dirname(os.path.abspath(__file__))
                token_path = os.path.join(current_dir, 'fb_token')
                
                with open(token_path, 'w') as file:
                    file.write(access_token)
                
                # Update the global token
                FB_ACCESS_TOKEN = access_token
                
                # Verify the token works
                verify_url = f"{FB_GRAPH_URL}/me"
                verify_params = {'access_token': access_token}
                verify_response = requests.get(verify_url, params=verify_params)
                verify_response.raise_for_status()
                user_data = verify_response.json()
                
                return {
                    "status": "success",
                    "message": f"Access token successfully refreshed and saved for user {user_data.get('name', 'Unknown')}",
                    "expires_in": data.get("expires_in", "unknown"),
                    "user_id": user_data.get("id")
                }
                
        except Exception as e:
            print(f"Error polling for token: {str(e)}")
    
    return {
        "status": "error",
        "message": f"Timeout: Authentication did not complete within {max_attempts*10} seconds"
    }

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"







if __name__ == "__main__":
    mcp.run(transport='stdio')
    # print(refresh_facebook_token(scope="ads_read"))