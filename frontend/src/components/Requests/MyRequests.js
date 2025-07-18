import React, { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import axios from 'axios'

const MyRequests = () => {
  const { session } = useAuth()
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchMyRequests()
  }, [session])

  const fetchMyRequests = async () => {
    try {
      setLoading(true)
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/requests/my`,
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`
          }
        }
      )
      setRequests(response.data)
    } catch (error) {
      console.error('Error fetching my requests:', error)
      setError('Failed to load your requests')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteRequest = async (requestId) => {
    if (!window.confirm('Are you sure you want to delete this request? You will get a full refund.')) {
      return
    }

    try {
      await axios.delete(
        `${process.env.REACT_APP_BACKEND_URL}/api/requests/${requestId}`,
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`
          }
        }
      )
      
      setRequests(prev => prev.filter(req => req.id !== requestId))
      alert('Request deleted successfully! Points have been refunded.')
    } catch (error) {
      console.error('Error deleting request:', error)
      alert('Failed to delete request')
    }
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

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
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
          onClick={fetchMyRequests}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">My Requests</h1>
        <p className="text-gray-600">
          View and manage your submitted feature requests
        </p>
      </div>

      {requests.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg">You haven't submitted any requests yet</div>
          <p className="text-gray-400 mt-2">Start by submitting your first feature request!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {requests.map((request) => (
            <div key={request.id} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {request.title}
                  </h3>
                  <p className="text-gray-600 mb-3">{request.description}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(request.status)}`}>
                    {formatStatus(request.status)}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-500">Category: {request.category}</p>
                  <p className="text-sm text-gray-500">Type: {request.request_type}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Priority: {request.priority}</p>
                  <p className="text-sm text-gray-500">Points spent: {request.points_spent}</p>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <div className="flex items-center space-x-1">
                    <span className="text-blue-600">👍</span>
                    <span>{request.votes} votes</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <span className="text-gray-600">💬</span>
                    <span>{request.comments_count} comments</span>
                  </div>
                  <span>Submitted {formatDate(request.submitted_at)}</span>
                </div>

                <div className="flex space-x-2">
                  {request.status === 'pending' && (
                    <button
                      onClick={() => handleDeleteRequest(request.id)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Delete
                    </button>
                  )}
                  <button
                    onClick={() => {
                      // TODO: Implement view details
                      console.log('View details for request:', request.id)
                    }}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    View Details
                  </button>
                </div>
              </div>

              {request.admin_notes && (
                <div className="mt-4 p-3 bg-gray-50 rounded-md">
                  <h4 className="text-sm font-medium text-gray-700 mb-1">Admin Notes:</h4>
                  <p className="text-sm text-gray-600">{request.admin_notes}</p>
                </div>
              )}

              {request.rejection_reason && (
                <div className="mt-4 p-3 bg-red-50 rounded-md">
                  <h4 className="text-sm font-medium text-red-700 mb-1">Rejection Reason:</h4>
                  <p className="text-sm text-red-600">{request.rejection_reason}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default MyRequests