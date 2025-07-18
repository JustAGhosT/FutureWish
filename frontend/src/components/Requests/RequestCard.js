import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import VoteModal from './VoteModal'
import axios from 'axios'

const RequestCard = ({ request, onVoteSubmitted, userPoints }) => {
  const { session } = useAuth()
  const [showVoteModal, setShowVoteModal] = useState(false)
  const [loading, setLoading] = useState(false)

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

  const getPriorityColor = (priority) => {
    const colors = {
      'low': 'bg-gray-100 text-gray-800',
      'medium': 'bg-blue-100 text-blue-800',
      'high': 'bg-orange-100 text-orange-800',
      'critical': 'bg-red-100 text-red-800'
    }
    return colors[priority] || colors.medium
  }

  const getCategoryColor = (category) => {
    const colors = {
      'ui_ux': 'bg-purple-100 text-purple-800',
      'performance': 'bg-green-100 text-green-800',
      'integration': 'bg-blue-100 text-blue-800',
      'security': 'bg-red-100 text-red-800',
      'mobile': 'bg-yellow-100 text-yellow-800',
      'api': 'bg-indigo-100 text-indigo-800',
      'other': 'bg-gray-100 text-gray-800'
    }
    return colors[category] || colors.other
  }

  const formatCategory = (category) => {
    return category.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const formatStatus = (status) => {
    return status.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const formatRequestType = (type) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const formatPriority = (priority) => {
    return priority.charAt(0).toUpperCase() + priority.slice(1)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const canVote = () => {
    return request.status === 'approved' && userPoints >= 1
  }

  const handleVoteSuccess = () => {
    setShowVoteModal(false)
    onVoteSubmitted()
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
              {request.title}
            </h3>
            <p className="text-gray-600 text-sm mb-3 line-clamp-3">
              {request.description}
            </p>
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mb-4">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
            {formatStatus(request.status)}
          </span>
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(request.category)}`}>
            {formatCategory(request.category)}
          </span>
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(request.priority)}`}>
            {formatPriority(request.priority)}
          </span>
        </div>

        {/* Request Type */}
        <div className="mb-4">
          <span className="text-sm text-gray-500">
            {formatRequestType(request.request_type)} • {request.points_spent} points spent
          </span>
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between mb-4 text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <span className="text-blue-600">👍</span>
              <span>{request.votes} votes</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="text-gray-600">💬</span>
              <span>{request.comments_count} comments</span>
            </div>
          </div>
          <div className="text-xs text-gray-500">
            {formatDate(request.submitted_at)}
          </div>
        </div>

        {/* Submitted by */}
        <div className="mb-4">
          <span className="text-sm text-gray-500">
            Submitted by {request.user_name || 'Anonymous'}
          </span>
        </div>

        {/* Additional Details */}
        {request.use_case && (
          <div className="mb-3">
            <h4 className="text-sm font-medium text-gray-700 mb-1">Use Case:</h4>
            <p className="text-sm text-gray-600 line-clamp-2">{request.use_case}</p>
          </div>
        )}

        {request.expected_behavior && (
          <div className="mb-3">
            <h4 className="text-sm font-medium text-gray-700 mb-1">Expected Behavior:</h4>
            <p className="text-sm text-gray-600 line-clamp-2">{request.expected_behavior}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex space-x-2">
          {canVote() ? (
            <button
              onClick={() => setShowVoteModal(true)}
              disabled={loading}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
            >
              {loading ? 'Loading...' : 'Vote'}
            </button>
          ) : (
            <button
              disabled
              className="flex-1 bg-gray-300 text-gray-500 py-2 px-4 rounded-md cursor-not-allowed text-sm"
            >
              {request.status === 'pending' ? 'Pending Review' : 
               request.status === 'rejected' ? 'Rejected' :
               request.status === 'implemented' ? 'Implemented' :
               userPoints < 1 ? 'Insufficient Points' : 'Cannot Vote'}
            </button>
          )}
          
          <button
            className="px-4 py-2 text-blue-600 border border-blue-600 rounded-md hover:bg-blue-50 transition-colors text-sm"
            onClick={() => {
              // TODO: Implement view details modal
              console.log('View details for request:', request.id)
            }}
          >
            Details
          </button>
        </div>

        {/* Admin Actions (if user is admin) */}
        {request.status === 'pending' && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  // TODO: Implement admin approve
                  console.log('Admin approve request:', request.id)
                }}
                className="flex-1 bg-green-600 text-white py-1 px-3 rounded text-xs hover:bg-green-700"
              >
                Approve
              </button>
              <button
                onClick={() => {
                  // TODO: Implement admin reject
                  console.log('Admin reject request:', request.id)
                }}
                className="flex-1 bg-red-600 text-white py-1 px-3 rounded text-xs hover:bg-red-700"
              >
                Reject
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Vote Modal */}
      {showVoteModal && (
        <VoteModal
          request={request}
          userPoints={userPoints}
          onClose={() => setShowVoteModal(false)}
          onSuccess={handleVoteSuccess}
        />
      )}
    </>
  )
}

export default RequestCard