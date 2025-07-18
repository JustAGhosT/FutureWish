import React, { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import RequestCard from './RequestCard'
import RequestForm from './RequestForm'
import axios from 'axios'

const RequestList = () => {
  const { session } = useAuth()
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showRequestForm, setShowRequestForm] = useState(false)
  const [userProfile, setUserProfile] = useState(null)
  const [filter, setFilter] = useState({
    status: '',
    category: '',
    request_type: '',
    priority: ''
  })

  useEffect(() => {
    fetchRequests()
    fetchUserProfile()
  }, [session, filter])

  const fetchRequests = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filter.status) params.append('status', filter.status)
      if (filter.category) params.append('category', filter.category)
      if (filter.request_type) params.append('request_type', filter.request_type)
      if (filter.priority) params.append('priority', filter.priority)
      
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/requests?${params}`,
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`
          }
        }
      )
      setRequests(response.data)
    } catch (error) {
      console.error('Error fetching requests:', error)
      setError('Failed to load requests')
    } finally {
      setLoading(false)
    }
  }

  const fetchUserProfile = async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/auth/me`,
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`
          }
        }
      )
      setUserProfile(response.data)
    } catch (error) {
      console.error('Error fetching user profile:', error)
    }
  }

  const handleRequestSubmitted = (newRequest) => {
    setRequests(prev => [newRequest, ...prev])
    fetchUserProfile() // Refresh user profile to update points
    alert(`Request submitted successfully! You spent ${newRequest.points_spent} points.`)
  }

  const handleVoteSubmitted = () => {
    fetchRequests() // Refresh requests to update vote counts
    fetchUserProfile() // Refresh user profile to update points
  }

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'approved': 'bg-green-100 text-green-800',
      'rejected': 'bg-red-100 text-red-800',
      'implemented': 'bg-blue-100 text-blue-800',
      'duplicate': 'bg-gray-100 text-gray-800'
    }
    return colors[status] || colors.pending
  }

  const formatStatus = (status) => {
    return status.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
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
          onClick={fetchRequests}
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
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Feature Requests</h1>
            <p className="text-gray-600">
              Submit and vote on feature requests to shape the platform's future
            </p>
          </div>
          <button
            onClick={() => setShowRequestForm(true)}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Submit Request</span>
          </button>
        </div>

        {userProfile && (
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-blue-900 mb-1">Your Points</h3>
                <p className="text-2xl font-bold text-blue-600">{userProfile.points}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-blue-700">
                  <strong>Request Costs:</strong> Feature (25) • Enhancement (15) • Bug Fix (10) • Integration (35)
                </p>
                <p className="text-sm text-blue-700">
                  <strong>Voting:</strong> 1-10 points per vote
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="mb-6 bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={filter.status}
              onChange={(e) => setFilter({...filter, status: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="implemented">Implemented</option>
              <option value="duplicate">Duplicate</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={filter.category}
              onChange={(e) => setFilter({...filter, category: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              <option value="ui_ux">UI/UX</option>
              <option value="performance">Performance</option>
              <option value="integration">Integration</option>
              <option value="security">Security</option>
              <option value="mobile">Mobile</option>
              <option value="api">API</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type
            </label>
            <select
              value={filter.request_type}
              onChange={(e) => setFilter({...filter, request_type: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              <option value="feature">Feature</option>
              <option value="enhancement">Enhancement</option>
              <option value="bug_fix">Bug Fix</option>
              <option value="integration">Integration</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Priority
            </label>
            <select
              value={filter.priority}
              onChange={(e) => setFilter({...filter, priority: e.target.value})}
              className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Priorities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
        </div>
      </div>

      {/* Request List */}
      {requests.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg">No requests found</div>
          <p className="text-gray-400 mt-2">Be the first to submit a feature request!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {requests.map((request) => (
            <RequestCard
              key={request.id}
              request={request}
              onVoteSubmitted={handleVoteSubmitted}
              userPoints={userProfile?.points || 0}
            />
          ))}
        </div>
      )}

      {/* Request Form Modal */}
      {showRequestForm && (
        <RequestForm
          onClose={() => setShowRequestForm(false)}
          onSuccess={handleRequestSubmitted}
        />
      )}
    </div>
  )
}

export default RequestList