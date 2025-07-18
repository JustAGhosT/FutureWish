import React, { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import GitHubSyncModal from './GitHubSyncModal'
import GitHubStats from './GitHubStats'
import axios from 'axios'

const GitHubIntegration = () => {
  const { session } = useAuth()
  const [integrations, setIntegrations] = useState([])
  const [gitHubStatus, setGitHubStatus] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showSyncModal, setShowSyncModal] = useState(false)
  const [selectedRequest, setSelectedRequest] = useState(null)

  useEffect(() => {
    fetchData()
  }, [session])

  const fetchData = async () => {
    try {
      setLoading(true)
      await Promise.all([
        fetchGitHubStatus(),
        fetchIntegrations(),
        fetchStats()
      ])
    } catch (error) {
      console.error('Error fetching GitHub data:', error)
      setError('Failed to load GitHub integration data')
    } finally {
      setLoading(false)
    }
  }

  const fetchGitHubStatus = async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/github/status`,
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`
          }
        }
      )
      setGitHubStatus(response.data)
    } catch (error) {
      console.error('Error fetching GitHub status:', error)
    }
  }

  const fetchIntegrations = async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/github/integrations`,
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`
          }
        }
      )
      setIntegrations(response.data)
    } catch (error) {
      console.error('Error fetching integrations:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/github/stats`,
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`
          }
        }
      )
      setStats(response.data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const handleSync = async (requestId) => {
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/github/sync/${requestId}`,
        {},
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`
          }
        }
      )
      
      alert('Successfully synced to GitHub!')
      fetchData() // Refresh data
    } catch (error) {
      console.error('Error syncing to GitHub:', error)
      alert(error.response?.data?.detail || 'Failed to sync to GitHub')
    }
  }

  const getSyncStatusColor = (status) => {
    const colors = {
      'not_synced': 'bg-gray-100 text-gray-800',
      'syncing': 'bg-yellow-100 text-yellow-800',
      'synced': 'bg-green-100 text-green-800',
      'sync_error': 'bg-red-100 text-red-800'
    }
    return colors[status] || colors.not_synced
  }

  const formatSyncStatus = (status) => {
    return status.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 text-lg font-medium">{error}</div>
        <button 
          onClick={fetchData}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">GitHub Integration</h1>
        <p className="text-gray-600">
          Sync feature requests with GitHub issues for seamless development workflow
        </p>
      </div>

      {/* GitHub Status */}
      <div className="mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            GitHub Configuration Status
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${
                gitHubStatus?.is_configured ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <span className="text-sm">
                {gitHubStatus?.is_configured ? 'GitHub API Connected' : 'GitHub API Not Connected'}
              </span>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${
                gitHubStatus?.webhook_secret_configured ? 'bg-green-500' : 'bg-yellow-500'
              }`}></div>
              <span className="text-sm">
                {gitHubStatus?.webhook_secret_configured ? 'Webhook Secret Configured' : 'Webhook Secret Missing'}
              </span>
            </div>
          </div>
          
          {gitHubStatus?.repository && (
            <div className="mt-4 p-3 bg-gray-50 rounded-md">
              <p className="text-sm text-gray-700">
                <strong>Repository:</strong> 
                <a 
                  href={gitHubStatus.repository.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 ml-1"
                >
                  {gitHubStatus.repository.owner}/{gitHubStatus.repository.name}
                </a>
              </p>
            </div>
          )}
        </div>
      </div>

      {/* GitHub Stats */}
      {stats && <GitHubStats stats={stats} />}

      {/* Integration List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">GitHub Integrations</h2>
        </div>
        
        <div className="px-6 py-4">
          {integrations.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-500 text-lg">No GitHub integrations found</div>
              <p className="text-gray-400 mt-2">Sync approved feature requests to GitHub issues</p>
            </div>
          ) : (
            <div className="space-y-4">
              {integrations.map((integration) => (
                <div key={integration.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900">
                        {integration.request_title}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Request ID: {integration.request_id}
                      </p>
                      <p className="text-sm text-gray-600">
                        Status: {integration.request_status}
                      </p>
                    </div>
                    
                    <div className="flex items-center space-x-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSyncStatusColor(integration.sync_status)}`}>
                        {formatSyncStatus(integration.sync_status)}
                      </span>
                      
                      {integration.github_issue_url ? (
                        <a
                          href={integration.github_issue_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 text-sm"
                        >
                          View Issue #{integration.github_issue_number}
                        </a>
                      ) : (
                        integration.sync_status === 'not_synced' && (
                          <button
                            onClick={() => handleSync(integration.request_id)}
                            className="text-blue-600 hover:text-blue-800 text-sm"
                          >
                            Sync to GitHub
                          </button>
                        )
                      )}
                    </div>
                  </div>
                  
                  {integration.last_sync_at && (
                    <p className="text-xs text-gray-500 mt-2">
                      Last synced: {formatDate(integration.last_sync_at)}
                    </p>
                  )}
                  
                  {integration.sync_error && (
                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                      <p className="text-sm text-red-600">{integration.sync_error}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Sync Modal */}
      {showSyncModal && (
        <GitHubSyncModal
          request={selectedRequest}
          onClose={() => setShowSyncModal(false)}
          onSuccess={() => {
            setShowSyncModal(false)
            fetchData()
          }}
        />
      )}
    </div>
  )
}

export default GitHubIntegration