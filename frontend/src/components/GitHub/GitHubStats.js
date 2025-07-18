import React from 'react'

const GitHubStats = ({ stats }) => {
  if (!stats) return null

  const getSuccessRate = () => {
    return Math.round(stats.sync_success_rate * 100)
  }

  return (
    <div className="mb-8">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          GitHub Sync Statistics
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {stats.total_integrations}
            </div>
            <div className="text-sm text-gray-600">Total Integrations</div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">
              {stats.synced_integrations}
            </div>
            <div className="text-sm text-gray-600">Synced to GitHub</div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">
              {stats.total_issues_created}
            </div>
            <div className="text-sm text-gray-600">Issues Created</div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-indigo-600 mb-2">
              {getSuccessRate()}%
            </div>
            <div className="text-sm text-gray-600">Success Rate</div>
          </div>
        </div>
        
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">Sync Status</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Synced</span>
                <span className="text-sm font-medium text-green-600">
                  {stats.synced_integrations}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Pending</span>
                <span className="text-sm font-medium text-yellow-600">
                  {stats.pending_integrations}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Errors</span>
                <span className="text-sm font-medium text-red-600">
                  {stats.error_integrations}
                </span>
              </div>
            </div>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">Repository Info</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Repository</span>
                <span className="text-sm font-medium">
                  {stats.repository_info?.full_name || 'Not configured'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">API Status</span>
                <span className={`text-sm font-medium ${
                  stats.repository_info?.is_configured ? 'text-green-600' : 'text-red-600'
                }`}>
                  {stats.repository_info?.is_configured ? 'Connected' : 'Not Connected'}
                </span>
              </div>
              {stats.last_sync_at && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Last Sync</span>
                  <span className="text-sm font-medium">
                    {new Date(stats.last_sync_at).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GitHubStats