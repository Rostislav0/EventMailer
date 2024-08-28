def generate_sql_query_minsk(ip_addresses):
    ipv4_addresses = [ip for ip in ip_addresses if ':' not in ip]
    ipv6_addresses = [ip for ip in ip_addresses if ':' in ip]

    ipv4_list = ', '.join([f"INET_ATON('{ip}') & ig.mask" for ip in ipv4_addresses])
    ipv6_list = ', '.join([f"HEX(inet6_mask(UNHEX(HEX(INET6_ATON('{ip}'))), UNHEX(HEX(INET6_ATON(inet_ntoa_ipv6("
                           f"ig.mask, ig.mask_ext))))))" for ip in ipv6_addresses])
    ipv6_check = ''
    if ipv6_addresses:
        ipv6_check = f"""OR  HEX(INET6_ATON(inet_ntoa_ipv6(ig.ip, ig.ip_ext)))
                    IN (
                        {ipv6_list}
                    )"""
    sql_query = f"""SELECT  
    a.id,
    u.full_name,
    COALESCE(
        (SELECT value 
         FROM user_additional_params 
         WHERE paramid = 12 AND userid = u.id 
         LIMIT 1), 
        u.email
    ) AS email,
    IF(ig.ip_ext <> 0 AND ig.mask_ext <> 0, 
        CONCAT(INET6_NTOA(INET6_ATON(inet_ntoa_ipv6(ig.ip, ig.ip_ext))), '/', IFNULL(64 - LOG(2, ABS(ig.mask)), 0) + 64 - LOG(2, ABS(ig.mask_ext))),
        CONCAT(INET_NTOA(ig.ip & 0xFFFFFFFF), '/', IFNULL(32 - LOG(2, ABS(ig.mask)), 0))) AS addr 
    FROM 
        ip_groups AS ig
        JOIN iptraffic_service_links AS isl ON isl.ip_group_id = ig.ip_group_id
        JOIN service_links AS sl ON isl.id = sl.id
        JOIN accounts AS a ON sl.account_id = a.id
        JOIN users_accounts AS ua ON ua.account_id = a.id
        JOIN users AS u ON u.id = ua.uid
    WHERE 
        ua.is_deleted = 0 
        AND ig.is_deleted = 0 
        AND sl.is_deleted = 0 
        AND isl.is_deleted = 0
        AND ((ig.mask <> 0 AND (ig.ip 
                    IN (
                        {ipv4_list}
                    )))
                {ipv6_check}
                );"""

    return sql_query


def generate_sql_query_gomel(ip_addresses):
    ip_conditions = " OR ".join([f"INET_ATON('{ip}') & ig.mask = ig.ip" for ip in ip_addresses])

    sql_query = f"""
    SELECT 
      a.id, 
      u.full_name, 
      COALESCE(
        (SELECT value 
         FROM user_additional_params 
         WHERE paramid = 12 AND userid = u.id 
         LIMIT 1), 
        u.email
      ) AS email, 
      CONCAT(INET_NTOA(ig.ip & 0xFFFFFFFF), '/', IFNULL(32 - LOG(2, ABS(ig.mask)), 0)) AS addr 
    FROM ip_groups AS ig 
    JOIN iptraffic_service_links AS isl ON isl.ip_group_id = ig.ip_group_id 
    JOIN service_links AS sl ON isl.id = sl.id 
    JOIN accounts AS a ON sl.account_id = a.id 
    JOIN users_accounts AS ua ON ua.account_id = a.id 
    JOIN users AS u ON u.id = ua.uid 
    WHERE ua.is_deleted = 0 
      AND ig.is_deleted = 0 
      AND sl.is_deleted = 0 
      AND isl.is_deleted = 0 
      AND ig.ip <> 0 
      AND ({ip_conditions});
    """
    return sql_query
