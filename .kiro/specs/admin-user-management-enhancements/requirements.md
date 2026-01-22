# Requirements Document

## Introduction

This document specifies the requirements for enhancing the admin user management system with additional endpoints for managing user permissions, menus, status control, and a new system information monitoring module.

## Glossary

- **Admin_User_API**: The FastAPI router module handling admin user management endpoints
- **System_Info_API**: The FastAPI router module providing system monitoring and information endpoints
- **RBAC_Service**: The Role-Based Access Control service managing permissions and menus
- **Permission_Override**: User-specific permission settings that override role-based permissions
- **Menu_Override**: User-specific menu visibility settings that override role-based menus
- **API_Log**: Database records of API requests and responses
- **Redis**: In-memory data store used for caching and session management
- **CPU_Usage**: Percentage of CPU resources being utilized by the system
- **Memory_Usage**: Amount of RAM being used by the system
- **Network_Stats**: Network interface statistics including bytes sent/received

## Requirements

### Requirement 1: Clear All Permission Overrides

**User Story:** As an administrator, I want to clear all permission overrides for a specific user, so that the user's permissions revert to their role-based permissions only.

#### Acceptance Criteria

1. WHEN an administrator requests to clear all permission overrides for a user, THE Admin_User_API SHALL remove all permission override records for that user
2. WHEN permission overrides are cleared, THE System SHALL mark all override records as deleted (soft delete)
3. WHEN the operation completes successfully, THE Admin_User_API SHALL return a success response with status code 200
4. IF the specified user does not exist, THEN THE Admin_User_API SHALL return an error response with status code 404

### Requirement 2: Clear All Menu Overrides

**User Story:** As an administrator, I want to clear all menu overrides for a specific user, so that the user's menu visibility reverts to their role-based menus only.

#### Acceptance Criteria

1. WHEN an administrator requests to clear all menu overrides for a user, THE Admin_User_API SHALL remove all menu override records for that user
2. WHEN menu overrides are cleared, THE System SHALL mark all override records as deleted (soft delete)
3. WHEN the operation completes successfully, THE Admin_User_API SHALL return a success response with status code 200
4. IF the specified user does not exist, THEN THE Admin_User_API SHALL return an error response with status code 404

### Requirement 3: View Complete User Menus

**User Story:** As an administrator, I want to view the complete menu structure for a specific user (including role-based menus and overrides), so that I can understand what menus the user can access.

#### Acceptance Criteria

1. WHEN an administrator requests a user's complete menus, THE Admin_User_API SHALL compute the union of all role-based menus for that user
2. WHEN computing menus, THE System SHALL apply menu overrides (ALLOW adds menus, DENY removes menus)
3. WHEN returning menus, THE Admin_User_API SHALL return only active menus (status = 1)
4. WHEN returning menus, THE Admin_User_API SHALL structure the response as a tree hierarchy
5. THE Admin_User_API SHALL reuse the existing menu computation logic from the authentication flow

### Requirement 4: View Complete User Permissions (Paginated)

**User Story:** As an administrator, I want to view a paginated list of all permissions for a specific user (including role-based permissions and overrides), so that I can audit and manage user access rights.

#### Acceptance Criteria

1. WHEN an administrator requests a user's permissions, THE Admin_User_API SHALL accept page and page_size as required parameters
2. WHEN computing permissions, THE System SHALL compute the union of all role-based permissions for that user
3. WHEN computing permissions, THE System SHALL apply permission overrides (ALLOW adds permissions, DENY removes permissions)
4. WHEN returning permissions, THE Admin_User_API SHALL return only active permissions (status = 1)
5. WHEN returning permissions, THE Admin_User_API SHALL return paginated results with total count, page number, page size, and permission items
6. WHEN no keyword filter is provided, THE System SHALL return all computed permissions
7. WHERE a keyword filter is provided, THE System SHALL filter permissions by API path or permission name

### Requirement 5: Toggle Admin User Status

**User Story:** As an administrator, I want to enable or disable admin user accounts, so that I can control user access to the system without deleting accounts.

#### Acceptance Criteria

1. WHEN an administrator requests to change a user's status, THE Admin_User_API SHALL accept user_id and is_active (boolean) as parameters
2. WHEN the status is changed, THE System SHALL update the user's is_active field in the database
3. WHEN a user is disabled (is_active = false), THE Auth_Middleware SHALL reject authentication attempts for that user
4. WHEN a disabled user attempts to access protected endpoints, THE Auth_Middleware SHALL return status code 401 with message "账户已被禁用"
5. WHEN the operation completes successfully, THE Admin_User_API SHALL return a success response with status code 200
6. IF the specified user does not exist, THEN THE Admin_User_API SHALL return an error response with status code 404
7. THE System SHALL prevent administrators from disabling their own account

### Requirement 6: System CPU and Memory Monitoring

**User Story:** As an administrator, I want to view the backend server's CPU and memory usage, so that I can monitor system resource utilization.

#### Acceptance Criteria

1. WHEN an administrator requests system information, THE System_Info_API SHALL return current CPU usage as a percentage
2. WHEN an administrator requests system information, THE System_Info_API SHALL return current memory usage including total, used, available, and percentage
3. THE System_Info_API SHALL use the psutil library to gather system metrics
4. WHEN the operation completes successfully, THE System_Info_API SHALL return a success response with status code 200

### Requirement 7: Network Statistics Monitoring

**User Story:** As an administrator, I want to view network interface statistics, so that I can monitor network activity and bandwidth usage.

#### Acceptance Criteria

1. WHEN an administrator requests network statistics, THE System_Info_API SHALL return bytes sent and bytes received for all network interfaces
2. WHEN an administrator requests network statistics, THE System_Info_API SHALL return packets sent and packets received
3. THE System_Info_API SHALL use the psutil library to gather network statistics
4. WHEN the operation completes successfully, THE System_Info_API SHALL return a success response with status code 200

### Requirement 8: Redis Connection Status

**User Story:** As an administrator, I want to view Redis connection status and basic information, so that I can verify the cache system is functioning properly.

#### Acceptance Criteria

1. WHEN an administrator requests Redis information, THE System_Info_API SHALL check if Redis is connected
2. WHEN Redis is connected, THE System_Info_API SHALL return connection status as true and include Redis server information
3. WHEN Redis is not connected, THE System_Info_API SHALL return connection status as false with an error message
4. WHEN Redis is connected, THE System_Info_API SHALL return database size (number of keys)
5. WHEN Redis is connected, THE System_Info_API SHALL return memory usage information
6. WHEN the operation completes successfully, THE System_Info_API SHALL return a success response with status code 200

### Requirement 9: Redis Key-Value Inspection

**User Story:** As an administrator, I want to view and search Redis key-value pairs, so that I can inspect cached data and debug issues.

#### Acceptance Criteria

1. WHEN an administrator requests Redis keys, THE System_Info_API SHALL accept page and page_size as required parameters
2. WHERE a pattern filter is provided, THE System_Info_API SHALL filter keys matching the pattern (using Redis SCAN command)
3. WHEN no pattern is provided, THE System_Info_API SHALL return all keys
4. WHEN returning key-value pairs, THE System_Info_API SHALL include key name, value type, and value content
5. WHEN a value is too large (> 1000 characters), THE System_Info_API SHALL truncate it with an indicator
6. WHEN the operation completes successfully, THE System_Info_API SHALL return paginated results with total count
7. IF Redis is not connected, THEN THE System_Info_API SHALL return an error response with status code 503

### Requirement 10: Failed Login Attempts Monitoring

**User Story:** As an administrator, I want to view the count of failed login attempts, so that I can monitor security threats and potential attacks.

#### Acceptance Criteria

1. WHEN an administrator requests failed login statistics, THE System_Info_API SHALL query the API_Log table
2. WHEN querying failed logins, THE System SHALL filter records where path = '/api/admin/auth/login'
3. WHEN querying failed logins, THE System SHALL filter records where status_code != 200
4. WHERE a time range is provided (start_date, end_date), THE System_Info_API SHALL filter records within that range
5. WHEN no time range is provided, THE System_Info_API SHALL return the total count of all failed login attempts
6. WHEN the operation completes successfully, THE System_Info_API SHALL return the count and optionally a breakdown by time period
7. THE System_Info_API SHALL return a success response with status code 200
