# server.py
from mcp.server.fastmcp import FastMCP
import requests
from typing import Dict, List, Optional, Any
import json
import requests
import sys

    

# --- Constants ---
FB_API_VERSION = "v22.0"
FB_GRAPH_URL = f"https://graph.facebook.com/{FB_API_VERSION}"
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
    """
    Get Facebook access token from command line arguments.
    Caches the token in memory after first read.

    Returns:
        str: The Facebook access token.

    Raises:
        Exception: If no token is provided in command line arguments.
    """
    global FB_ACCESS_TOKEN
    if FB_ACCESS_TOKEN is None:
        # Look for --fb-token argument
        if "--fb-token" in sys.argv:
            token_index = sys.argv.index("--fb-token") + 1
            if token_index < len(sys.argv):
                FB_ACCESS_TOKEN = sys.argv[token_index]
                print(f"Using Facebook token from command line arguments")
            else:
                raise Exception("--fb-token argument provided but no token value followed it")
        else:
            raise Exception("Facebook token must be provided via '--fb-token' command line argument")

    return FB_ACCESS_TOKEN

def _make_graph_api_call(url: str, params: Dict[str, Any]) -> Dict:
    """Makes a GET request to the Facebook Graph API and handles the response."""
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        # Log the error and re-raise or handle more gracefully
        print(f"Error making Graph API call to {url} with params {params}: {e}")
        # Depending on desired behavior, you might want to raise a custom exception
        # or return a specific error structure. Re-raising keeps the current behavior.
        raise


def _prepare_params(base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Adds optional parameters to a dictionary if they are not None. Handles JSON encoding."""
    params = base_params.copy()
    for key, value in kwargs.items():
        if value is not None:
            # Parameters that need JSON encoding
            if key in ['filtering', 'time_range', 'time_ranges', 'effective_status', 
                       'special_ad_categories', 'objective', 
                       'buyer_guarantee_agreement_status'] and isinstance(value, (list, dict)):
                params[key] = json.dumps(value)
            elif key == 'fields' and isinstance(value, list):
                 params[key] = ','.join(value)
            elif key == 'action_attribution_windows' and isinstance(value, list):
                 params[key] = ','.join(value)
            elif key == 'action_breakdowns' and isinstance(value, list):
                 params[key] = ','.join(value)
            elif key == 'breakdowns' and isinstance(value, list):
                 params[key] = ','.join(value)
            else:
                params[key] = value
    return params


def _fetch_node(node_id: str, **kwargs) -> Dict:
    """Helper to fetch a single object (node) by its ID."""
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{node_id}"
    params = _prepare_params({'access_token': access_token}, **kwargs)
    return _make_graph_api_call(url, params)

def _fetch_edge(parent_id: str, edge_name: str, **kwargs) -> Dict:
    """Helper to fetch a collection (edge) related to a parent object."""
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{parent_id}/{edge_name}"
    
    # Handle time parameters specifically for activities edge if needed
    time_params = {}
    if edge_name == 'activities':
        time_range = kwargs.pop('time_range', None)
        since = kwargs.pop('since', None)
        until = kwargs.pop('until', None)
        if time_range:
            time_params['time_range'] = time_range
        else:
            if since: time_params['since'] = since
            if until: time_params['until'] = until
            
    base_params = {'access_token': access_token}
    params = _prepare_params(base_params, **kwargs)
    params.update(_prepare_params({}, **time_params)) # Add specific time params

    return _make_graph_api_call(url, params)


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
    
    # Use the generic parameter builder first
    params = _prepare_params(
        params,
        fields=fields,
        level=level,
        action_attribution_windows=action_attribution_windows,
        action_breakdowns=action_breakdowns,
        action_report_time=action_report_time,
        breakdowns=breakdowns,
        filtering=filtering,
        sort=sort,
        limit=limit,
        after=after,
        before=before,
        offset=offset,
        locale=locale
    )

    # Handle time parameters (specific logic for insights)
    time_params_provided = time_range or time_ranges or since or until
    if not time_params_provided and date_preset:
        params['date_preset'] = date_preset
    if time_range:
        params['time_range'] = json.dumps(time_range)
    if time_ranges:
        params['time_ranges'] = json.dumps(time_ranges)
    if time_increment and time_increment != 'all_days': # API default is all_days
        params['time_increment'] = time_increment
        
    # Time-based pagination (only if specific time range isn't set)
    if not time_range and not time_ranges:
        if since:
            params['since'] = since
        if until:
            params['until'] = until

    # Boolean flags need specific handling ('true'/'false' strings)
    if default_summary:
        params['default_summary'] = 'true'
    if use_account_attribution_setting:
        params['use_account_attribution_setting'] = 'true'
    # Only add unified if True (it defaults to False in API if omitted)
    if use_unified_attribution_setting:
        params['use_unified_attribution_setting'] = 'true'

    return params



# --- MCP Tools ---
@mcp.tool()
def list_ad_accounts() -> Dict:
    """List down the ad accounts and their names associated with your Facebook account"""
    # This uses a specific endpoint structure not fitting _fetch_node/_fetch_edge easily
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/me"
    params = {
        'access_token': access_token,
        'fields': 'adaccounts{name}' # Specific field structure
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
    effective_fields = fields if fields is not None else DEFAULT_AD_ACCOUNT_FIELDS
    return _fetch_node(node_id=act_id, fields=effective_fields)


# --- Insigbts API Tools ---

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


# --- Ad Creative Tools ---

@mcp.tool()
def get_ad_creative_by_id(
    creative_id: str, 
    fields: Optional[List[str]] = None,
    thumbnail_width: Optional[int] = None, 
    thumbnail_height: Optional[int] = None
) -> Dict:
    """Retrieves detailed information about a specific Facebook ad creative.

    This tool interfaces with the Facebook Graph API to fetch comprehensive details
    about an ad creative, such as its name, status, specifications, engagement metrics,
    and associated objects (like images, videos, and pages).

    Args:
        creative_id (str): The ID of the ad creative to retrieve.
        fields (Optional[List[str]]): A list of specific fields to retrieve. If None, 
            returns the default set of fields. Available fields include (but are not limited to):
            - 'account_id': Ad account ID the creative belongs to
            - 'actor_id': ID of the Facebook actor (page/app/person) associated with this creative
            - 'adlabels': Ad labels associated with this creative
            - 'applink_treatment': App link treatment type
            - 'asset_feed_spec': Specifications for dynamic ad creatives
            - 'authorization_category': For political ads, shows authorization category
            - 'body': Ad body text content
            - 'branded_content_sponsor_page_id': ID of the sponsor page for branded content
            - 'call_to_action_type': Type of call to action button
            - 'effective_authorization_category': Effective authorization category for the ad
            - 'effective_instagram_media_id': Instagram media ID used in the ad
            - 'effective_instagram_story_id': Instagram story ID used in the ad
            - 'effective_object_story_id': Object story ID used for the ad
            - 'id': Creative ID
            - 'image_hash': Hash of the image used in the creative
            - 'image_url': URL of the image used
            - 'instagram_actor_id': Instagram actor ID associated with creative (deprecated)
            - 'instagram_permalink_url': Instagram permalink URL
            - 'instagram_story_id': Instagram story ID
            - 'instagram_user_id': Instagram user ID associated with creative
            - 'link_og_id': Open Graph ID for the link
            - 'link_url': URL being advertised
            - 'name': Name of the creative in the ad account library
            - 'object_id': ID of the Facebook object being advertised
            - 'object_story_id': ID of the page post used in the ad
            - 'object_story_spec': Specification for the page post to create for the ad
            - 'object_type': Type of the object being advertised
            - 'object_url': URL of the object being advertised
            - 'platform_customizations': Custom specifications for different platforms
            - 'product_set_id': ID of the product set for product ads
            - 'status': Status of this creative (ACTIVE, IN_PROCESS, WITH_ISSUES, DELETED)
            - 'template_url': URL of the template used
            - 'thumbnail_url': URL of the creative thumbnail
            - 'title': Ad headline/title text
            - 'url_tags': URL tags appended to landing pages for tracking
            - 'use_page_actor_override': Use the page actor instead of ad account actor
            - 'video_id': ID of the video used in the ad
        
        thumbnail_width (Optional[int]): Width of the thumbnail in pixels. Default: 64.
        thumbnail_height (Optional[int]): Height of the thumbnail in pixels. Default: 64.

    Returns:
        Dict: A dictionary containing the requested ad creative details.

    Example:
        ```python
        # Get basic information about an ad creative
        creative = get_ad_creative_details(
            creative_id="23842312323312",
            fields=["name", "status", "object_story_id", "thumbnail_url"]
        )
        
        # Get a larger thumbnail with specific dimensions
        creative_with_thumbnail = get_ad_creative_details(
            creative_id="23842312323312", 
            fields=["name", "thumbnail_url"],
            thumbnail_width=300,
            thumbnail_height=200
        )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{creative_id}"
    params = {'access_token': access_token}
    
    # Add requested fields
    if fields:
        params['fields'] = ','.join(fields)
    
    # Add thumbnail dimensions if specified
    if thumbnail_width:
        params['thumbnail_width'] = thumbnail_width
    if thumbnail_height:
        params['thumbnail_height'] = thumbnail_height
    
    return _make_graph_api_call(url, params)


@mcp.tool()
def get_ad_creatives_by_ad_id(
    ad_id: str,
    fields: Optional[List[str]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    date_format: Optional[str] = None
) -> Dict:
    """Retrieves the ad creatives associated with a specific Facebook ad.
    
    This function accesses the Facebook Graph API to retrieve the creative objects
    used by a specific ad, including details about the creative content, media, 
    and specifications.
    
    Args:
        ad_id (str): The ID of the ad to retrieve creatives for.
        fields (Optional[List[str]]): A list of specific fields to retrieve for each creative.
            If None, a default set of fields will be returned. Available fields include:
            - 'id': The creative's ID
            - 'name': The creative's name
            - 'account_id': The ID of the ad account this creative belongs to
            - 'actor_id': ID of the Facebook actor associated with creative
            - 'adlabels': Ad labels applied to the creative
            - 'applink_treatment': App link treatment type
            - 'asset_feed_spec': Specifications for dynamic ad creatives
            - 'authorization_category': Political ad authorization category
            - 'body': Ad body text content
            - 'branded_content_sponsor_page_id': ID of sponsoring page for branded content
            - 'call_to_action_type': Type of call to action button
            - 'effective_authorization_category': Effective authorization category
            - 'effective_instagram_media_id': Instagram media ID used
            - 'effective_instagram_story_id': Instagram story ID used
            - 'effective_object_story_id': Object story ID used
            - 'image_hash': Hash of the image used in the creative
            - 'image_url': URL of the image used
            - 'instagram_actor_id': Instagram actor ID (deprecated)
            - 'instagram_permalink_url': Instagram permalink URL
            - 'instagram_story_id': Instagram story ID
            - 'instagram_user_id': Instagram user ID associated with creative
            - 'link_og_id': Open Graph ID for the link
            - 'link_url': URL being advertised
            - 'object_id': ID of the Facebook object being advertised
            - 'object_story_id': ID of the page post used in the ad
            - 'object_story_spec': Specification for the page post 
            - 'object_type': Type of the object being advertised ('PAGE', 'DOMAIN', etc.)
            - 'object_url': URL of the object being advertised
            - 'platform_customizations': Custom specifications for different platforms
            - 'product_set_id': ID of the product set for product ads
            - 'status': Status of this creative ('ACTIVE', 'IN_PROCESS', etc.)
            - 'template_url': URL of the template used
            - 'thumbnail_url': URL of the creative thumbnail
            - 'title': Ad headline/title text
            - 'url_tags': URL tags appended to landing pages for tracking
            - 'use_page_actor_override': Whether to use the page actor instead of account actor
            - 'video_id': ID of the video used in the ad
        limit (Optional[int]): Maximum number of creatives to return per page. Default is 25.
        after (Optional[str]): Pagination cursor for the next page. From response['paging']['cursors']['after'].
        before (Optional[str]): Pagination cursor for the previous page. From response['paging']['cursors']['before'].
        date_format (Optional[str]): Format for date responses. Options:
            - 'U': Unix timestamp (seconds since epoch)
            - 'Y-m-d H:i:s': MySQL datetime format
            - None: ISO 8601 format (default)
    
    Returns:
        Dict: A dictionary containing the requested ad creatives. The main results are in the 'data'
              list, and pagination info is in the 'paging' object.
    
    Example:
        ```python
        # Get basic creative information for an ad
        creatives = get_ad_creatives(
            ad_id="23843211234567",
            fields=["name", "image_url", "body", "title", "status"]
        )
        
        # Get detailed creative specifications with pagination
        detailed_creatives = get_ad_creatives(
            ad_id="23843211234567",
            fields=["name", "object_story_spec", "image_url", "call_to_action_type"],
            limit=50
        )
        
        # Fetch the next page if available using the pagination cursor
        next_page_cursor = creatives.get("paging", {}).get("cursors", {}).get("after")
        if next_page_cursor:
            next_page = get_ad_creatives(
                ad_id="23843211234567",
                fields=["name", "image_url", "body", "title"],
                limit=50,
                after=next_page_cursor
            )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{ad_id}/adcreatives"
    params = {
        'access_token': access_token
    }
    
    if fields:
        params['fields'] = ','.join(fields)
    
    if limit is not None:
        params['limit'] = limit
    
    if after:
        params['after'] = after
    
    if before:
        params['before'] = before
        
    if date_format:
        params['date_format'] = date_format
    
    return _make_graph_api_call(url, params)


# --- Ad Tools ---

@mcp.tool()
def get_ad_by_id(ad_id: str, fields: Optional[List[str]] = None) -> Dict:
    """Retrieves detailed information about a specific Facebook ad by its ID.
    
    This function accesses the Facebook Graph API to retrieve information about a
    single ad object, including details about its status, targeting, creative, budget,
    and performance metrics.
    
    Args:
        ad_id (str): The ID of the ad to retrieve information for.
        fields (Optional[List[str]]): A list of specific fields to retrieve. If None,
            a default set of fields will be returned. Available fields include:
            - 'id': The ad's ID
            - 'name': The ad's name
            - 'account_id': The ID of the ad account this ad belongs to
            - 'adset_id': The ID of the ad set this ad belongs to
            - 'campaign_id': The ID of the campaign this ad belongs to
            - 'adlabels': Labels applied to the ad
            - 'bid_amount': The bid amount for this ad
            - 'bid_type': The bid type of this ad
            - 'bid_info': The bid info for this ad
            - 'configured_status': The configured status of this ad
            - 'conversion_domain': The conversion domain for this ad
            - 'created_time': When the ad was created
            - 'creative': The ad creative
            - 'effective_status': The effective status of this ad
            - 'issues_info': Information about issues with this ad
            - 'recommendations': Recommendations for improving this ad
            - 'status': The status of this ad
            - 'tracking_specs': The tracking specs for this ad
            - 'updated_time': When this ad was last updated
            - 'preview_shareable_link': Link for previewing this ad
    
    Returns:
        Dict: A dictionary containing the requested ad information.
    
    Example:
        ```python
        # Get basic ad information
        ad = get_ad_by_id(
            ad_id="23843211234567",
            fields=["name", "adset_id", "campaign_id", "effective_status", "creative"]
        )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{ad_id}"
    params = {
        'access_token': access_token
    }
    
    if fields:
        params['fields'] = ','.join(fields)
    
    return _make_graph_api_call(url, params)


@mcp.tool()
def get_ads_by_adaccount(
    act_id: str,
    fields: Optional[List[str]] = None,
    filtering: Optional[List[dict]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    date_preset: Optional[str] = None,
    time_range: Optional[Dict[str, str]] = None,
    updated_since: Optional[int] = None,
    effective_status: Optional[List[str]] = None
) -> Dict:
    """Retrieves ads from a specific Facebook ad account.
    
    This function allows querying all ads belonging to a specific ad account with
    various filtering options, pagination, and field selection.
    
    Args:
        act_id (str): The ID of the ad account to retrieve ads from, prefixed with 'act_', 
                      e.g., 'act_1234567890'.
        fields (Optional[List[str]]): A list of specific fields to retrieve for each ad. 
                                      If None, a default set of fields will be returned.
                                      Common fields include:
            - 'id': The ad's ID
            - 'name': The ad's name
            - 'adset_id': The ID of the ad set this ad belongs to
            - 'campaign_id': The ID of the campaign this ad belongs to
            - 'creative': The ad creative details
            - 'status': The current status of the ad
            - 'effective_status': The effective status including review status
            - 'bid_amount': The bid amount for this ad
            - 'configured_status': The configured status
            - 'created_time': When the ad was created
            - 'updated_time': When the ad was last updated
            - 'targeting': Targeting criteria
            - 'conversion_specs': Conversion specs
            - 'recommendations': Recommendations for improving the ad
            - 'preview_shareable_link': Link for previewing the ad
        filtering (Optional[List[dict]]): A list of filter objects to apply to the data.
                                         Each object should have 'field', 'operator', and 'value' keys.
        limit (Optional[int]): Maximum number of ads to return per page. Default is 25.
        after (Optional[str]): Pagination cursor for the next page. From response['paging']['cursors']['after'].
        before (Optional[str]): Pagination cursor for the previous page. From response['paging']['cursors']['before'].
        date_preset (Optional[str]): A predefined relative date range for selecting ads.
                                    Options include 'today', 'yesterday', 'this_week', etc.
        time_range (Optional[Dict[str, str]]): A custom time range with 'since' and 'until' 
                                              dates in 'YYYY-MM-DD' format.
        updated_since (Optional[int]): Return ads that have been updated since this Unix timestamp.
        effective_status (Optional[List[str]]): Filter ads by their effective status. 
                                               Options include: 'ACTIVE', 'PAUSED', 'DELETED', 
                                               'PENDING_REVIEW', 'DISAPPROVED', 'PREAPPROVED', 
                                               'PENDING_BILLING_INFO', 'CAMPAIGN_PAUSED', 'ARCHIVED', 
                                               'ADSET_PAUSED', 'IN_PROCESS', 'WITH_ISSUES'.
    
    Returns:
        Dict: A dictionary containing the requested ads. The main results are in the 'data'
              list, and pagination info is in the 'paging' object.
    
    Example:
        ```python
        # Get active ads from an ad account
        ads = get_ads_by_adaccount(
            act_id="act_123456789",
            fields=["name", "adset_id", "campaign_id", "effective_status", "created_time"],
            effective_status=["ACTIVE"],
            limit=50
        )
        
        # Fetch the next page if available using the pagination cursor
        next_page_cursor = ads.get("paging", {}).get("cursors", {}).get("after")
        if next_page_cursor:
            next_page = get_ads_by_adaccount(
                act_id="act_123456789",
                fields=["name", "adset_id", "campaign_id", "effective_status", "created_time"],
                effective_status=["ACTIVE"],
                limit=50,
                after=next_page_cursor
            )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/ads"
    params = {
        'access_token': access_token
    }
    
    if fields:
        params['fields'] = ','.join(fields)
    
    if filtering:
        params['filtering'] = json.dumps(filtering)
    
    if limit is not None:
        params['limit'] = limit
    
    if after:
        params['after'] = after
    
    if before:
        params['before'] = before
    
    if date_preset:
        params['date_preset'] = date_preset
    
    if time_range:
        params['time_range'] = json.dumps(time_range)
    
    if updated_since:
        params['updated_since'] = updated_since
    
    if effective_status:
        params['effective_status'] = json.dumps(effective_status)
    
    return _make_graph_api_call(url, params)


@mcp.tool()
def get_ads_by_campaign(
    campaign_id: str,
    fields: Optional[List[str]] = None,
    filtering: Optional[List[dict]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    effective_status: Optional[List[str]] = None
) -> Dict:
    """Retrieves ads associated with a specific Facebook campaign.
    
    This function allows querying all ads belonging to a specific campaign,
    with filtering options, pagination, and field selection.
    
    Args:
        campaign_id (str): The ID of the campaign to retrieve ads from.
        fields (Optional[List[str]]): A list of specific fields to retrieve for each ad.
                                      If None, a default set of fields will be returned.
                                      Common fields include:
            - 'id': The ad's ID
            - 'name': The ad's name
            - 'adset_id': The ID of the ad set this ad belongs to
            - 'creative': The ad creative details
            - 'status': The current status of the ad
            - 'effective_status': The effective status including review status
            - 'bid_amount': The bid amount for this ad
            - 'created_time': When the ad was created
            - 'updated_time': When the ad was last updated
            - 'targeting': Targeting criteria
            - 'preview_shareable_link': Link for previewing the ad
        filtering (Optional[List[dict]]): A list of filter objects to apply to the data.
                                         Each object should have 'field', 'operator', and 'value' keys.
        limit (Optional[int]): Maximum number of ads to return per page. Default is 25.
        after (Optional[str]): Pagination cursor for the next page. From response['paging']['cursors']['after'].
        before (Optional[str]): Pagination cursor for the previous page. From response['paging']['cursors']['before'].
        effective_status (Optional[List[str]]): Filter ads by their effective status.
                                               Options include: 'ACTIVE', 'PAUSED', 'DELETED',
                                               'PENDING_REVIEW', 'DISAPPROVED', 'PREAPPROVED',
                                               'PENDING_BILLING_INFO', 'ADSET_PAUSED', 'ARCHIVED',
                                               'IN_PROCESS', 'WITH_ISSUES'.
    
    Returns:
        Dict: A dictionary containing the requested ads. The main results are in the 'data'
              list, and pagination info is in the 'paging' object.
    
    Example:
        ```python
        # Get all active ads from a campaign
        ads = get_ads_by_campaign(
            campaign_id="23843211234567",
            fields=["name", "adset_id", "effective_status", "created_time"],
            effective_status=["ACTIVE"],
            limit=50
        )
        
        # Fetch the next page if available using the pagination cursor
        next_page_cursor = ads.get("paging", {}).get("cursors", {}).get("after")
        if next_page_cursor:
            next_page = get_ads_by_campaign(
                campaign_id="23843211234567",
                fields=["name", "adset_id", "effective_status", "created_time"],
                effective_status=["ACTIVE"],
                limit=50,
                after=next_page_cursor
            )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{campaign_id}/ads"
    params = {
        'access_token': access_token
    }
    
    if fields:
        params['fields'] = ','.join(fields)
    
    if filtering:
        params['filtering'] = json.dumps(filtering)
    
    if limit is not None:
        params['limit'] = limit
    
    if after:
        params['after'] = after
    
    if before:
        params['before'] = before
    
    if effective_status:
        params['effective_status'] = json.dumps(effective_status)
    
    return _make_graph_api_call(url, params)


@mcp.tool()
def get_ads_by_adset(
    adset_id: str,
    fields: Optional[List[str]] = None,
    filtering: Optional[List[dict]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    effective_status: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> Dict:
    """Retrieves ads associated with a specific Facebook ad set.
    
    This function allows querying all ads belonging to a specific ad set,
    with filtering options, pagination, and field selection.
    
    Args:
        adset_id (str): The ID of the ad set to retrieve ads from.
        fields (Optional[List[str]]): A list of specific fields to retrieve for each ad.
                                      If None, a default set of fields will be returned.
                                      See get_ad_by_id for a comprehensive list of available fields.
        filtering (Optional[List[dict]]): A list of filter objects to apply to the data.
                                         Each object should have 'field', 'operator', and 'value' keys.
                                         Operators include: 'EQUAL', 'NOT_EQUAL', 'GREATER_THAN',
                                         'GREATER_THAN_OR_EQUAL', 'LESS_THAN', 'LESS_THAN_OR_EQUAL',
                                         'IN_RANGE', 'NOT_IN_RANGE', 'CONTAIN', 'NOT_CONTAIN',
                                         'IN', 'NOT_IN', 'EMPTY', 'NOT_EMPTY'.
        limit (Optional[int]): Maximum number of ads to return per page. Default is 25, max is 100.
        after (Optional[str]): Pagination cursor for the next page. From response['paging']['cursors']['after'].
        before (Optional[str]): Pagination cursor for the previous page. From response['paging']['cursors']['before'].
        effective_status (Optional[List[str]]): Filter ads by their effective status.
                                               Options include: 'ACTIVE', 'PAUSED', 'DELETED',
                                               'PENDING_REVIEW', 'DISAPPROVED', 'PREAPPROVED',
                                               'PENDING_BILLING_INFO', 'CAMPAIGN_PAUSED', 'ARCHIVED',
                                               'IN_PROCESS', 'WITH_ISSUES'.
        date_format (Optional[str]): Format for date responses. Options:
                                    - 'U': Unix timestamp (seconds since epoch)
                                    - 'Y-m-d H:i:s': MySQL datetime format
                                    - None: ISO 8601 format (default)
    
    Returns:
        Dict: A dictionary containing the requested ads. The main results are in the 'data'
              list, and pagination info is in the 'paging' object.
    
    Example:
        ```python
        # Get all active ads from an ad set
        ads = get_ads_by_adset(
            adset_id="23843211234567",
            fields=["name", "campaign_id", "effective_status", "created_time", "creative"],
            effective_status=["ACTIVE"],
            limit=50
        )
        
        # Get ads with specific fields and date format
        time_ads = get_ads_by_adset(
            adset_id="23843211234567",
            fields=["name", "created_time", "updated_time", "status"],
            date_format="Y-m-d H:i:s"
        )
        
        # Fetch the next page if available using the pagination cursor
        next_page_cursor = ads.get("paging", {}).get("cursors", {}).get("after")
        if next_page_cursor:
            next_page = get_ads_by_adset(
                adset_id="23843211234567",
                fields=["name", "campaign_id", "effective_status", "created_time", "creative"],
                effective_status=["ACTIVE"],
                limit=50,
                after=next_page_cursor
            )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{adset_id}/ads"
    params = {
        'access_token': access_token
    }
    
    if fields:
        params['fields'] = ','.join(fields)
    
    if filtering:
        params['filtering'] = json.dumps(filtering)
    
    if limit is not None:
        params['limit'] = limit
    
    if after:
        params['after'] = after
    
    if before:
        params['before'] = before
    
    if effective_status:
        params['effective_status'] = json.dumps(effective_status)
        
    if date_format:
        params['date_format'] = date_format
    
    return _make_graph_api_call(url, params)


# --- Ad Set Tools ---

@mcp.tool()
def get_adset_by_id(adset_id: str, fields: Optional[List[str]] = None) -> Dict:
    """Retrieves detailed information about a specific Facebook ad set by its ID.
    
    This function accesses the Facebook Graph API to retrieve information about a
    single ad set, including details about its targeting, budget, scheduling, and status.
    
    Args:
        adset_id (str): The ID of the ad set to retrieve information for.
        fields (Optional[List[str]]): A list of specific fields to retrieve. If None,
            a default set of fields will be returned. Available fields include:
            - 'id': The ad set's ID
            - 'name': The ad set's name
            - 'account_id': The ID of the ad account this ad set belongs to
            - 'campaign_id': The ID of the campaign this ad set belongs to
            - 'bid_amount': The bid amount for this ad set
            - 'bid_strategy': Strategy used for bidding. Options include: 'LOWEST_COST_WITHOUT_CAP', 
                'LOWEST_COST_WITH_BID_CAP', 'COST_CAP'
            - 'billing_event': The billing event type. Options include: 'APP_INSTALLS', 
                'CLICKS', 'IMPRESSIONS', 'LINK_CLICKS', 'NONE', 'OFFER_CLAIMS', 
                'PAGE_LIKES', 'POST_ENGAGEMENT', 'THRUPLAY'
            - 'budget_remaining': The remaining budget for this ad set (in cents/smallest currency unit)
            - 'configured_status': The status set by the user. Options include: 'ACTIVE', 
                'PAUSED', 'DELETED', 'ARCHIVED'
            - 'created_time': When the ad set was created
            - 'daily_budget': The daily budget for this ad set (in cents/smallest currency unit)
            - 'daily_min_spend_target': The minimum daily spend target (in cents/smallest currency unit)
            - 'daily_spend_cap': The daily spend cap (in cents/smallest currency unit)
            - 'destination_type': Type of destination for the ads
            - 'effective_status': The effective status (actual status). Options include: 'ACTIVE', 
                'PAUSED', 'DELETED', 'PENDING_REVIEW', 'DISAPPROVED', 'PREAPPROVED', 
                'PENDING_BILLING_INFO', 'CAMPAIGN_PAUSED', 'ARCHIVED', 'ADSET_PAUSED', 
                'IN_PROCESS', 'WITH_ISSUES'
            - 'end_time': When the ad set will end (in ISO 8601 format)
            - 'frequency_control_specs': Specifications for frequency control
            - 'lifetime_budget': The lifetime budget (in cents/smallest currency unit)
            - 'lifetime_imps': The maximum number of lifetime impressions
            - 'lifetime_min_spend_target': The minimum lifetime spend target
            - 'lifetime_spend_cap': The lifetime spend cap
            - 'optimization_goal': The optimization goal for this ad set. Options include: 
                'APP_INSTALLS', 'BRAND_AWARENESS', 'CLICKS', 'ENGAGED_USERS', 'EVENT_RESPONSES', 
                'IMPRESSIONS', 'LEAD_GENERATION', 'LINK_CLICKS', 'NONE', 'OFFER_CLAIMS', 
                'OFFSITE_CONVERSIONS', 'PAGE_ENGAGEMENT', 'PAGE_LIKES', 'POST_ENGAGEMENT', 
                'QUALITY_LEAD', 'REACH', 'REPLIES', 'SOCIAL_IMPRESSIONS', 'THRUPLAY', 
                'VALUE', 'VISIT_INSTAGRAM_PROFILE'
            - 'pacing_type': List of pacing types. Options include: 'standard', 'no_pacing'
            - 'promoted_object': The object this ad set is promoting
            - 'recommendations': Recommendations for improving this ad set
            - 'rf_prediction_id': The Reach and Frequency prediction ID
            - 'source_adset_id': ID of the source ad set if this is a copy
            - 'start_time': When the ad set starts (in ISO 8601 format)
            - 'status': Deprecated. The ad set's status. Use 'effective_status' instead.
            - 'targeting': The targeting criteria for this ad set (complex object)
            - 'time_based_ad_rotation_id_blocks': Time-based ad rotation blocks
            - 'time_based_ad_rotation_intervals': Time-based ad rotation intervals in seconds
            - 'updated_time': When this ad set was last updated
            - 'use_new_app_click': Whether to use the newer app click tracking
    
    Returns:
        Dict: A dictionary containing the requested ad set information.
    
    Example:
        ```python
        # Get basic ad set information
        adset = get_adset_by_id(
            adset_id="23843211234567",
            fields=["name", "campaign_id", "effective_status", "targeting", "budget_remaining"]
        )
        
        # Get detailed scheduling information
        adset_schedule = get_adset_by_id(
            adset_id="23843211234567",
            fields=["name", "start_time", "end_time", "daily_budget", "lifetime_budget"]
        )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{adset_id}"
    params = {
        'access_token': access_token
    }
    
    if fields:
        params['fields'] = ','.join(fields)
    
    return _make_graph_api_call(url, params)


@mcp.tool()
def get_adsets_by_ids(
    adset_ids: List[str],
    fields: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> Dict:
    """Retrieves detailed information about multiple Facebook ad sets by their IDs.
    
    This function allows batch retrieval of multiple ad sets in a single API call,
    improving efficiency when you need data for several ad sets.
    
    Args:
        adset_ids (List[str]): A list of ad set IDs to retrieve information for.
        fields (Optional[List[str]]): A list of specific fields to retrieve for each ad set.
            If None, a default set of fields will be returned. See get_adset_by_id for
            a comprehensive list of available fields.
        date_format (Optional[str]): Format for date responses. Options:
            - 'U': Unix timestamp (seconds since epoch)
            - 'Y-m-d H:i:s': MySQL datetime format
            - None: ISO 8601 format (default)
    
    Returns:
        Dict: A dictionary where keys are the ad set IDs and values are the
              corresponding ad set details.
    
    Example:
        ```python
        # Get information for multiple ad sets
        adsets = get_adsets_by_ids(
            adset_ids=["23843211234567", "23843211234568", "23843211234569"],
            fields=["name", "campaign_id", "effective_status", "budget_remaining"],
            date_format="U"  # Get dates as Unix timestamps
        )
        
        # Access information for a specific ad set
        if "23843211234567" in adsets:
            print(adsets["23843211234567"]["name"])
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/"
    params = {
        'access_token': access_token,
        'ids': ','.join(adset_ids)
    }
    
    if fields:
        params['fields'] = ','.join(fields)
        
    if date_format:
        params['date_format'] = date_format
    
    return _make_graph_api_call(url, params)


@mcp.tool()
def get_adsets_by_adaccount(
    act_id: str,
    fields: Optional[List[str]] = None,
    filtering: Optional[List[dict]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    date_preset: Optional[str] = None,
    time_range: Optional[Dict[str, str]] = None,
    updated_since: Optional[int] = None,
    effective_status: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> Dict:
    """Retrieves ad sets from a specific Facebook ad account.
    
    This function allows querying all ad sets belonging to a specific ad account with
    various filtering options, pagination, and field selection.
    
    Args:
        act_id (str): The ID of the ad account to retrieve ad sets from, prefixed with 'act_', 
                      e.g., 'act_1234567890'.
        fields (Optional[List[str]]): A list of specific fields to retrieve for each ad set. 
                                      If None, a default set of fields will be returned.
                                      See get_adset_by_id for a comprehensive list of available fields.
        filtering (Optional[List[dict]]): A list of filter objects to apply to the data.
                                         Each object should have 'field', 'operator', and 'value' keys.
                                         Operators include: 'EQUAL', 'NOT_EQUAL', 'GREATER_THAN',
                                         'GREATER_THAN_OR_EQUAL', 'LESS_THAN', 'LESS_THAN_OR_EQUAL',
                                         'IN_RANGE', 'NOT_IN_RANGE', 'CONTAIN', 'NOT_CONTAIN',
                                         'IN', 'NOT_IN', 'EMPTY', 'NOT_EMPTY'.
                                         Example: [{'field': 'daily_budget', 'operator': 'GREATER_THAN', 'value': 1000}]
        limit (Optional[int]): Maximum number of ad sets to return per page. Default is 25, max is 100.
        after (Optional[str]): Pagination cursor for the next page. From response['paging']['cursors']['after'].
        before (Optional[str]): Pagination cursor for the previous page. From response['paging']['cursors']['before'].
        date_preset (Optional[str]): A predefined relative date range for selecting ad sets.
                                    Options include: 'today', 'yesterday', 'this_month', 'last_month', 
                                    'this_quarter', 'lifetime', 'last_3d', 'last_7d', 'last_14d', 
                                    'last_28d', 'last_30d', 'last_90d', 'last_quarter', 'last_year', 
                                    'this_week_mon_today', 'this_week_sun_today', 'this_year'.
        time_range (Optional[Dict[str, str]]): A custom time range with 'since' and 'until' 
                                              dates in 'YYYY-MM-DD' format.
                                              Example: {'since': '2023-01-01', 'until': '2023-01-31'}
        updated_since (Optional[int]): Return ad sets that have been updated since this Unix timestamp.
        effective_status (Optional[List[str]]): Filter ad sets by their effective status. 
                                               Options include: 'ACTIVE', 'PAUSED', 'DELETED', 
                                               'PENDING_REVIEW', 'DISAPPROVED', 'PREAPPROVED', 
                                               'PENDING_BILLING_INFO', 'CAMPAIGN_PAUSED', 'ARCHIVED', 
                                               'WITH_ISSUES'.
        date_format (Optional[str]): Format for date responses. Options:
                                    - 'U': Unix timestamp (seconds since epoch)
                                    - 'Y-m-d H:i:s': MySQL datetime format
                                    - None: ISO 8601 format (default)
    
    Returns:
        Dict: A dictionary containing the requested ad sets. The main results are in the 'data'
              list, and pagination info is in the 'paging' object.
    
    Example:
        ```python
        # Get active ad sets from an ad account
        adsets = get_adsets_by_adaccount(
            act_id="act_123456789",
            fields=["name", "campaign_id", "effective_status", "daily_budget", "targeting"],
            effective_status=["ACTIVE"],
            limit=50
        )
        
        # Get ad sets with daily budget above a certain amount
        high_budget_adsets = get_adsets_by_adaccount(
            act_id="act_123456789",
            fields=["name", "daily_budget", "lifetime_budget"],
            filtering=[{'field': 'daily_budget', 'operator': 'GREATER_THAN', 'value': 5000}],
            limit=100
        )
        
        # Fetch the next page if available using the pagination cursor
        next_page_cursor = adsets.get("paging", {}).get("cursors", {}).get("after")
        if next_page_cursor:
            next_page = get_adsets_by_adaccount(
                act_id="act_123456789",
                fields=["name", "campaign_id", "effective_status", "daily_budget"],
                effective_status=["ACTIVE"],
                limit=50,
                after=next_page_cursor
            )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/adsets"
    params = {
        'access_token': access_token
    }
    
    if fields:
        params['fields'] = ','.join(fields)
    
    if filtering:
        params['filtering'] = json.dumps(filtering)
    
    if limit is not None:
        params['limit'] = limit
    
    if after:
        params['after'] = after
    
    if before:
        params['before'] = before
    
    if date_preset:
        params['date_preset'] = date_preset
    
    if time_range:
        params['time_range'] = json.dumps(time_range)
    
    if updated_since:
        params['updated_since'] = updated_since
    
    if effective_status:
        params['effective_status'] = json.dumps(effective_status)
        
    if date_format:
        params['date_format'] = date_format
    
    return _make_graph_api_call(url, params)


@mcp.tool()
def get_adsets_by_campaign(
    campaign_id: str,
    fields: Optional[List[str]] = None,
    filtering: Optional[List[dict]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    effective_status: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> Dict:
    """Retrieves ad sets associated with a specific Facebook campaign.
    
    This function allows querying all ad sets belonging to a specific campaign,
    with filtering options, pagination, and field selection.
    
    Args:
        campaign_id (str): The ID of the campaign to retrieve ad sets from.
        fields (Optional[List[str]]): A list of specific fields to retrieve for each ad set.
                                      If None, a default set of fields will be returned.
                                      See get_adset_by_id for a comprehensive list of available fields.
        filtering (Optional[List[dict]]): A list of filter objects to apply to the data.
                                         Each object should have 'field', 'operator', and 'value' keys.
                                         Operators include: 'EQUAL', 'NOT_EQUAL', 'GREATER_THAN',
                                         'GREATER_THAN_OR_EQUAL', 'LESS_THAN', 'LESS_THAN_OR_EQUAL',
                                         'IN_RANGE', 'NOT_IN_RANGE', 'CONTAIN', 'NOT_CONTAIN',
                                         'IN', 'NOT_IN', 'EMPTY', 'NOT_EMPTY'.
                                         Example: [{'field': 'daily_budget', 'operator': 'GREATER_THAN', 'value': 1000}]
        limit (Optional[int]): Maximum number of ad sets to return per page. Default is 25, max is 100.
        after (Optional[str]): Pagination cursor for the next page. From response['paging']['cursors']['after'].
        before (Optional[str]): Pagination cursor for the previous page. From response['paging']['cursors']['before'].
        effective_status (Optional[List[str]]): Filter ad sets by their effective status.
                                               Options include: 'ACTIVE', 'PAUSED', 'DELETED',
                                               'PENDING_REVIEW', 'DISAPPROVED', 'PREAPPROVED',
                                               'PENDING_BILLING_INFO', 'ARCHIVED', 'WITH_ISSUES'.
        date_format (Optional[str]): Format for date responses. Options:
                                    - 'U': Unix timestamp (seconds since epoch)
                                    - 'Y-m-d H:i:s': MySQL datetime format
                                    - None: ISO 8601 format (default)
    
    Returns:
        Dict: A dictionary containing the requested ad sets. The main results are in the 'data'
              list, and pagination info is in the 'paging' object.
    
    Example:
        ```python
        # Get all active ad sets from a campaign
        adsets = get_adsets_by_campaign(
            campaign_id="23843211234567",
            fields=["name", "effective_status", "daily_budget", "targeting", "optimization_goal"],
            effective_status=["ACTIVE"],
            limit=50
        )
        
        # Get ad sets with specific optimization goals
        conversion_adsets = get_adsets_by_campaign(
            campaign_id="23843211234567",
            fields=["name", "optimization_goal", "billing_event", "bid_amount"],
            filtering=[{
                'field': 'optimization_goal', 
                'operator': 'IN', 
                'value': ['OFFSITE_CONVERSIONS', 'VALUE']
            }]
        )
        
        # Fetch the next page if available using the pagination cursor
        next_page_cursor = adsets.get("paging", {}).get("cursors", {}).get("after")
        if next_page_cursor:
            next_page = get_adsets_by_campaign(
                campaign_id="23843211234567",
                fields=["name", "effective_status", "daily_budget", "targeting"],
                effective_status=["ACTIVE"],
                limit=50,
                after=next_page_cursor
            )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{campaign_id}/adsets"
    params = {
        'access_token': access_token
    }
    
    if fields:
        params['fields'] = ','.join(fields)
    
    if filtering:
        params['filtering'] = json.dumps(filtering)
    
    if limit is not None:
        params['limit'] = limit
    
    if after:
        params['after'] = after
    
    if before:
        params['before'] = before
    
    if effective_status:
        params['effective_status'] = json.dumps(effective_status)
        
    if date_format:
        params['date_format'] = date_format
    
    return _make_graph_api_call(url, params)


# --- Campaign Tools ---
@mcp.tool()
def get_campaign_by_id(
    campaign_id: str, 
    fields: Optional[List[str]] = None,
    date_format: Optional[str] = None
) -> Dict:
    """Retrieves detailed information about a specific Facebook ad campaign by its ID.
    
    This function accesses the Facebook Graph API to retrieve information about a
    single campaign, including details about its objective, status, budget settings,
    and other campaign-level configurations.
    
    Args:
        campaign_id (str): The ID of the campaign to retrieve information for.
        fields (Optional[List[str]]): A list of specific fields to retrieve. If None,
            a default set of fields will be returned. Available fields include:
            - 'id': The campaign's ID
            - 'name': The campaign's name
            - 'account_id': The ID of the ad account this campaign belongs to
            - 'adlabels': Labels applied to the campaign
            - 'bid_strategy': The bid strategy for the campaign. Options include:
                'LOWEST_COST_WITHOUT_CAP', 'LOWEST_COST_WITH_BID_CAP', 'COST_CAP'
            - 'boosted_object_id': The ID of the boosted object
            - 'brand_lift_studies': Brand lift studies associated with this campaign
            - 'budget_rebalance_flag': Whether budget rebalancing is enabled
            - 'budget_remaining': The remaining budget (in cents/smallest currency unit)
            - 'buying_type': The buying type. Options include:
                'AUCTION', 'RESERVED', 'DEPRECATED_REACH_BLOCK'
            - 'can_create_brand_lift_study': Whether a brand lift study can be created
            - 'can_use_spend_cap': Whether a spend cap can be used
            - 'configured_status': Status set by the user. Options include:
                'ACTIVE', 'PAUSED', 'DELETED', 'ARCHIVED'
            - 'created_time': When the campaign was created
            - 'daily_budget': The daily budget (in cents/smallest currency unit)
            - 'effective_status': The effective status accounting for the ad account and other factors.
                Options include: 'ACTIVE', 'PAUSED', 'DELETED', 'PENDING_REVIEW', 'DISAPPROVED',
                'PREAPPROVED', 'PENDING_BILLING_INFO', 'CAMPAIGN_PAUSED', 'ARCHIVED', 'IN_PROCESS',
                'WITH_ISSUES'
            - 'has_secondary_skadnetwork_reporting': Whether secondary SKAdNetwork reporting is available
            - 'is_budget_schedule_enabled': Whether budget scheduling is enabled
            - 'is_skadnetwork_attribution': Whether the campaign uses SKAdNetwork attribution (iOS 14.5+)
            - 'issues_info': Information about issues with this campaign
            - 'last_budget_toggling_time': Last time the budget was toggled
            - 'lifetime_budget': The lifetime budget (in cents/smallest currency unit)
            - 'objective': The campaign's advertising objective. Options include:
                'APP_INSTALLS', 'BRAND_AWARENESS', 'CONVERSIONS', 'EVENT_RESPONSES',
                'LEAD_GENERATION', 'LINK_CLICKS', 'LOCAL_AWARENESS', 'MESSAGES',
                'OFFER_CLAIMS', 'PAGE_LIKES', 'POST_ENGAGEMENT', 'PRODUCT_CATALOG_SALES',
                'REACH', 'STORE_VISITS', 'VIDEO_VIEWS'
            - 'pacing_type': List of pacing types. Options include: 'standard', 'no_pacing'
            - 'primary_attribution': Primary attribution settings
            - 'promoted_object': The object this campaign is promoting
            - 'recommendations': Recommendations for improving this campaign
            - 'smart_promotion_type': Smart promotion type if applicable
            - 'source_campaign': Source campaign if this was created by copying
            - 'source_campaign_id': ID of the source campaign if copied
            - 'special_ad_categories': Array of special ad categories. Options include:
                'EMPLOYMENT', 'HOUSING', 'CREDIT', 'ISSUES_ELECTIONS_POLITICS', 'NONE'
            - 'special_ad_category': Special ad category (deprecated in favor of special_ad_categories)
            - 'spend_cap': The spending cap (in cents/smallest currency unit)
            - 'start_time': When the campaign starts (in ISO 8601 format unless date_format specified)
            - 'status': Deprecated. Use 'configured_status' or 'effective_status' instead
            - 'stop_time': When the campaign stops (in ISO 8601 format unless date_format specified)
            - 'topline_id': Topline ID for this campaign
            - 'updated_time': When this campaign was last updated
        date_format (Optional[str]): Format for date responses. Options:
            - 'U': Unix timestamp (seconds since epoch)
            - 'Y-m-d H:i:s': MySQL datetime format
            - None: ISO 8601 format (default)
    
    Returns:
        Dict: A dictionary containing the requested campaign information.
    
    Example:
        ```python
        # Get basic campaign information
        campaign = get_campaign_by_id(
            campaign_id="23843211234567",
            fields=["name", "objective", "effective_status", "budget_remaining"]
        )
        
        # Get detailed budget information with Unix timestamps
        campaign_budget_details = get_campaign_by_id(
            campaign_id="23843211234567",
            fields=["name", "daily_budget", "lifetime_budget", "start_time", "stop_time"],
            date_format="U"
        )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{campaign_id}"
    params = {
        'access_token': access_token
    }
    
    if fields:
        params['fields'] = ','.join(fields)
    
    if date_format:
        params['date_format'] = date_format
    
    return _make_graph_api_call(url, params)

@mcp.tool()
def get_campaigns_by_adaccount(
    act_id: str,
    fields: Optional[List[str]] = None,
    filtering: Optional[List[dict]] = None,
    limit: Optional[int] = 25,
    after: Optional[str] = None,
    before: Optional[str] = None,
    date_preset: Optional[str] = None,
    time_range: Optional[Dict[str, str]] = None,
    updated_since: Optional[int] = None,
    effective_status: Optional[List[str]] = None,
    is_completed: Optional[bool] = None,
    special_ad_categories: Optional[List[str]] = None,
    objective: Optional[List[str]] = None,
    buyer_guarantee_agreement_status: Optional[List[str]] = None,
    date_format: Optional[str] = None,
    include_drafts: Optional[bool] = None
) -> Dict:
    """Retrieves campaigns from a specific Facebook ad account.
    
    This function allows querying all campaigns belonging to a specific ad account with
    various filtering options, pagination, and field selection.
    
    Args:
        act_id (str): The ID of the ad account to retrieve campaigns from, prefixed with 'act_', 
                      e.g., 'act_1234567890'.
        fields (Optional[List[str]]): A list of specific fields to retrieve for each campaign.
                                      If None, a default set of fields will be returned.
                                      See get_campaign_by_id for a comprehensive list of available fields.
        filtering (Optional[List[dict]]): A list of filter objects to apply to the data.
                                         Each object should have 'field', 'operator', and 'value' keys.
                                         Operators include: 'EQUAL', 'NOT_EQUAL', 'GREATER_THAN',
                                         'GREATER_THAN_OR_EQUAL', 'LESS_THAN', 'LESS_THAN_OR_EQUAL',
                                         'IN_RANGE', 'NOT_IN_RANGE', 'CONTAIN', 'NOT_CONTAIN',
                                         'IN', 'NOT_IN', 'EMPTY', 'NOT_EMPTY'.
                                         Example: [{'field': 'daily_budget', 'operator': 'GREATER_THAN', 'value': 1000}]
        limit (Optional[int]): Maximum number of campaigns to return per page. Default is 25, max is 100.
        after (Optional[str]): Pagination cursor for the next page. From response['paging']['cursors']['after'].
        before (Optional[str]): Pagination cursor for the previous page. From response['paging']['cursors']['before'].
        date_preset (Optional[str]): A predefined relative date range for selecting campaigns.
                                    Options include: 'today', 'yesterday', 'this_month', 'last_month', 
                                    'this_quarter', 'maximum', 'last_3d', 'last_7d', 'last_14d', 
                                    'last_28d', 'last_30d', 'last_90d', 'last_week_mon_sun', 
                                    'last_week_sun_sat', 'last_quarter', 'last_year', 
                                    'this_week_mon_today', 'this_week_sun_today', 'this_year'.
        time_range (Optional[Dict[str, str]]): A custom time range with 'since' and 'until' 
                                              dates in 'YYYY-MM-DD' format.
                                              Example: {'since': '2023-01-01', 'until': '2023-01-31'}
        updated_since (Optional[int]): Return campaigns that have been updated since this Unix timestamp.
        effective_status (Optional[List[str]]): Filter campaigns by their effective status. 
                                               Options include: 'ACTIVE', 'PAUSED', 'DELETED', 
                                               'PENDING_REVIEW', 'DISAPPROVED', 'PREAPPROVED', 
                                               'PENDING_BILLING_INFO', 'ARCHIVED', 'WITH_ISSUES'.
        is_completed (Optional[bool]): If True, returns only completed campaigns. If False, returns 
                                      only active campaigns. If None, returns both.
        special_ad_categories (Optional[List[str]]): Filter campaigns by special ad categories.
                                                   Options include: 'EMPLOYMENT', 'HOUSING', 'CREDIT', 
                                                   'ISSUES_ELECTIONS_POLITICS', 'NONE'.
        objective (Optional[List[str]]): Filter campaigns by advertising objective.
                                      Options include: 'APP_INSTALLS', 'BRAND_AWARENESS', 
                                      'CONVERSIONS', 'EVENT_RESPONSES', 'LEAD_GENERATION', 
                                      'LINK_CLICKS', 'LOCAL_AWARENESS', 'MESSAGES', 'OFFER_CLAIMS', 
                                      'PAGE_LIKES', 'POST_ENGAGEMENT', 'PRODUCT_CATALOG_SALES', 
                                      'REACH', 'STORE_VISITS', 'VIDEO_VIEWS'.
        buyer_guarantee_agreement_status (Optional[List[str]]): Filter campaigns by buyer guarantee agreement status.
                                                              Options include: 'APPROVED', 'NOT_APPROVED'.
        date_format (Optional[str]): Format for date responses. Options:
                                    - 'U': Unix timestamp (seconds since epoch)
                                    - 'Y-m-d H:i:s': MySQL datetime format
                                    - None: ISO 8601 format (default)
        include_drafts (Optional[bool]): If True, includes draft campaigns in the results.
    
    Returns:
        Dict: A dictionary containing the requested campaigns. The main results are in the 'data'
              list, and pagination info is in the 'paging' object.
    
    Example:
        ```python
        # Get active campaigns from an ad account
        campaigns = get_campaigns_by_adaccount(
            act_id="act_123456789",
            fields=["name", "objective", "effective_status", "created_time"],
            effective_status=["ACTIVE"],
            limit=50
        )
        
        # Get campaigns with specific objectives
        lead_gen_campaigns = get_campaigns_by_adaccount(
            act_id="act_123456789",
            fields=["name", "objective", "spend_cap", "daily_budget"],
            objective=["LEAD_GENERATION", "CONVERSIONS"],
            date_format="U"
        )
        
        # Get campaigns created in a specific date range
        date_filtered_campaigns = get_campaigns_by_adaccount(
            act_id="act_123456789",
            fields=["name", "created_time", "objective"],
            time_range={"since": "2023-01-01", "until": "2023-01-31"}
        )
        
        # Fetch the next page if available using the pagination cursor
        next_page_cursor = campaigns.get("paging", {}).get("cursors", {}).get("after")
        if next_page_cursor:
            next_page = get_campaigns_by_adaccount(
                act_id="act_123456789",
                fields=["name", "objective", "effective_status", "created_time"],
                effective_status=["ACTIVE"],
                limit=50,
                after=next_page_cursor
            )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/campaigns"
    params = {
        'access_token': access_token
    }
    
    if fields:
        params['fields'] = ','.join(fields)
    
    if filtering:
        params['filtering'] = json.dumps(filtering)
    
    if limit is not None:
        params['limit'] = limit
    
    if after:
        params['after'] = after
    
    if before:
        params['before'] = before
    
    if date_preset:
        params['date_preset'] = date_preset
    
    if time_range:
        params['time_range'] = json.dumps(time_range)
    
    if updated_since:
        params['updated_since'] = updated_since
    
    if effective_status:
        params['effective_status'] = json.dumps(effective_status)
    
    if is_completed is not None:
        params['is_completed'] = is_completed
    
    if special_ad_categories:
        params['special_ad_categories'] = json.dumps(special_ad_categories)
    
    if objective:
        params['objective'] = json.dumps(objective)
    
    if buyer_guarantee_agreement_status:
        params['buyer_guarantee_agreement_status'] = json.dumps(buyer_guarantee_agreement_status)
    
    if date_format:
        params['date_format'] = date_format
    
    if include_drafts is not None:
        params['include_drafts'] = include_drafts
    
    return _make_graph_api_call(url, params)

# --- Activity Tools ---

@mcp.tool()
def get_activities_by_adaccount(
    act_id: str,
    fields: Optional[List[str]] = None,
    limit: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    time_range: Optional[Dict[str, str]] = None,
    since: Optional[str] = None,
    until: Optional[str] = None
) -> Dict:
    """Retrieves activities for a Facebook ad account.
    
    This function accesses the Facebook Graph API to retrieve information about 
    key updates to an ad account and ad objects associated with it. By default, 
    this API returns one week's data. Information returned includes major account 
    status changes, updates made to budget, campaign, targeting, audiences and more.
    
    Args:
        act_id (str): The ID of the ad account, prefixed with 'act_', e.g., 'act_1234567890'.
        fields (Optional[List[str]]): A list of specific fields to retrieve. If None,
            all available fields will be returned. Available fields include:
            - 'actor_id': ID of the user who made the change
            - 'actor_name': Name of the user who made the change
            - 'application_id': ID of the application used to make the change
            - 'application_name': Name of the application used to make the change
            - 'changed_data': Details about what was changed in JSON format
            - 'date_time_in_timezone': The timestamp in the account's timezone
            - 'event_time': The timestamp of when the event occurred
            - 'event_type': The specific type of change that was made (numeric code)
            - 'extra_data': Additional data related to the change in JSON format
            - 'object_id': ID of the object that was changed (ad, campaign, etc.)
            - 'object_name': Name of the object that was changed
            - 'object_type': Type of object being modified, values include:
              'AD', 'ADSET', 'CAMPAIGN', 'ACCOUNT', 'IMAGE', 'REPORT', etc.
            - 'translated_event_type': Human-readable description of the change made,
              examples include: 'ad created', 'campaign budget updated', 
              'targeting updated', 'ad status changed', etc.
        limit (Optional[int]): Maximum number of activities to return per page.
            Default behavior returns a server-determined number of results.
        after (Optional[str]): Pagination cursor for the next page of results.
            Obtained from the 'paging.cursors.after' field in the previous response.
        before (Optional[str]): Pagination cursor for the previous page of results.
            Obtained from the 'paging.cursors.before' field in the previous response.
        time_range (Optional[Dict[str, str]]): A custom time range with 'since' and 'until'
            dates in 'YYYY-MM-DD' format. Example: {'since': '2023-01-01', 'until': '2023-01-31'}
            This parameter overrides the since/until parameters if both are provided.
        since (Optional[str]): Start date in YYYY-MM-DD format. Defines the beginning 
            of the time range for returned activities. Ignored if 'time_range' is provided.
        until (Optional[str]): End date in YYYY-MM-DD format. Defines the end 
            of the time range for returned activities. Ignored if 'time_range' is provided.
    
    Returns:
        Dict: A dictionary containing the requested activities. The main results are in the 'data'
              list, and pagination info is in the 'paging' object. Each activity object contains
              information about who made the change, what was changed, when it occurred, and
              the specific details of the change.
    
    Example:
        ```python
        # Get recent activities for an ad account with default one week of data
        activities = get_activities_by_adaccount(
            act_id="act_123456789",
            fields=["event_time", "actor_name", "object_type", "translated_event_type"]
        )
        
        # Get all activities from a specific date range
        dated_activities = get_activities_by_adaccount(
            act_id="act_123456789",
            time_range={"since": "2023-01-01", "until": "2023-01-31"},
            fields=["event_time", "actor_name", "object_type", "translated_event_type", "extra_data"]
        )
        
        # Paginate through activity results
        paginated_activities = get_activities_by_adaccount(
            act_id="act_123456789",
            limit=50,
            fields=["event_time", "actor_name", "object_type", "translated_event_type"]
        )
        
        # Get the next page using the cursor from the previous response
        next_page_cursor = paginated_activities.get("paging", {}).get("cursors", {}).get("after")
        if next_page_cursor:
            next_page = get_activities_by_adaccount(
                act_id="act_123456789",
                fields=["event_time", "actor_name", "object_type", "translated_event_type"],
                after=next_page_cursor
            )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{act_id}/activities"
    params = {
        'access_token': access_token
    }
    
    if fields:
        params['fields'] = ','.join(fields)
    
    if limit is not None:
        params['limit'] = limit
    
    if after:
        params['after'] = after
    
    if before:
        params['before'] = before
    
    # time_range takes precedence over since/until
    if time_range:
        params['time_range'] = json.dumps(time_range)
    else:
        if since:
            params['since'] = since
        if until:
            params['until'] = until
    
    return _make_graph_api_call(url, params)




@mcp.tool()
def get_activities_by_adset(
    adset_id: str,
    fields: Optional[List[str]] = None,
    limit: Optional[int] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    time_range: Optional[Dict[str, str]] = None,
    since: Optional[str] = None,
    until: Optional[str] = None
) -> Dict:
    """Retrieves activities for a Facebook ad set.
    
    This function accesses the Facebook Graph API to retrieve information about 
    key updates to an ad set. By default, this API returns one week's data. 
    Information returned includes status changes, budget updates, targeting changes, and more.
    
    Args:
        adset_id (str): The ID of the ad set, e.g., '123456789'.
        fields (Optional[List[str]]): A list of specific fields to retrieve. If None,
            all available fields will be returned. Available fields include:
            - 'actor_id': ID of the user who made the change
            - 'actor_name': Name of the user who made the change
            - 'application_id': ID of the application used to make the change
            - 'application_name': Name of the application used to make the change
            - 'changed_data': Details about what was changed in JSON format
            - 'date_time_in_timezone': The timestamp in the account's timezone
            - 'event_time': The timestamp of when the event occurred
            - 'event_type': The specific type of change that was made (numeric code)
            - 'extra_data': Additional data related to the change in JSON format
            - 'object_id': ID of the object that was changed
            - 'object_name': Name of the object that was changed
            - 'object_type': Type of object being modified
            - 'translated_event_type': Human-readable description of the change made,
              examples include: 'adset created', 'adset budget updated', 
              'targeting updated', 'adset status changed', etc.
        limit (Optional[int]): Maximum number of activities to return per page.
            Default behavior returns a server-determined number of results.
        after (Optional[str]): Pagination cursor for the next page of results.
            Obtained from the 'paging.cursors.after' field in the previous response.
        before (Optional[str]): Pagination cursor for the previous page of results.
            Obtained from the 'paging.cursors.before' field in the previous response.
        time_range (Optional[Dict[str, str]]): A custom time range with 'since' and 'until'
            dates in 'YYYY-MM-DD' format. Example: {'since': '2023-01-01', 'until': '2023-01-31'}
            This parameter overrides the since/until parameters if both are provided.
        since (Optional[str]): Start date in YYYY-MM-DD format. Defines the beginning 
            of the time range for returned activities. Ignored if 'time_range' is provided.
        until (Optional[str]): End date in YYYY-MM-DD format. Defines the end 
            of the time range for returned activities. Ignored if 'time_range' is provided.
    
    Returns:
        Dict: A dictionary containing the requested activities. The main results are in the 'data'
              list, and pagination info is in the 'paging' object. Each activity object contains
              information about who made the change, what was changed, when it occurred, and
              the specific details of the change.
    
    Example:
        ```python
        # Get recent activities for an ad set with default one week of data
        activities = get_activities_by_adset(
            adset_id="123456789",
            fields=["event_time", "actor_name", "translated_event_type"]
        )
        
        # Get all activities from a specific date range
        dated_activities = get_activities_by_adset(
            adset_id="123456789",
            time_range={"since": "2023-01-01", "until": "2023-01-31"},
            fields=["event_time", "actor_name", "translated_event_type", "extra_data"]
        )
        
        # Paginate through activity results
        paginated_activities = get_activities_by_adset(
            adset_id="123456789",
            limit=50,
            fields=["event_time", "actor_name", "translated_event_type"]
        )
        ```
    """
    access_token = _get_fb_access_token()
    url = f"{FB_GRAPH_URL}/{adset_id}/activities"
    params = {
        'access_token': access_token
    }
    
    if fields:
        params['fields'] = ','.join(fields)
    
    if limit is not None:
        params['limit'] = limit
    
    if after:
        params['after'] = after
    
    if before:
        params['before'] = before
    
    # time_range takes precedence over since/until
    if time_range:
        params['time_range'] = json.dumps(time_range)
    else:
        if since:
            params['since'] = since
        if until:
            params['until'] = until
    
    return _make_graph_api_call(url, params)


if __name__ == "__main__":
    _get_fb_access_token()
    mcp.run(transport='stdio')
    