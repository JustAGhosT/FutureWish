import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import axios from 'axios'

const VoteModal = ({ request, userPoints, onClose, onSuccess }) => {
  const { session } = useAuth()
  const [pointsToSpend, setPointsToSpend] = useState(1)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (pointsToSpend < 1 || pointsToSpend > 10) {
      setError('You can vote with 1-10 points')
      return
    }

    if (pointsToSpend > userPoints) {
      setError('Insufficient points')
      return
    }

    try {
      setSubmitting(true)
      setError('')

      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/requests/${request.id}/vote`,
        { points_spent: pointsToSpend },
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      alert(`Vote submitted! You spent ${pointsToSpend} points. Remaining: ${response.data.remaining_points}`)
      onSuccess()
    } catch (error) {
      console.error('Error voting:', error)
      setError(error.response?.data?.detail || 'Failed to submit vote')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Vote on Request</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mb-4">
          <h4 className="font-medium text-gray-900 mb-2">{request.title}</h4>
          <p className="text-sm text-gray-600">{request.description}</p>
        </div>

        <div className="mb-4 p-3 bg-blue-50 rounded-md">
          <p className="text-sm text-blue-800">
            <strong>Current votes:</strong> {request.votes} points
          </p>
          <p className="text-sm text-blue-800">
            <strong>Your available points:</strong> {userPoints}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Points to spend (1-10)
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={pointsToSpend}
              onChange={(e) => setPointsToSpend(parseInt(e.target.value))}
              className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              More points = stronger vote. Range: 1-10 points
            </p>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || pointsToSpend > userPoints}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {submitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Voting...</span>
                </>
              ) : (
                <>
                  <span>Vote</span>
                  <span className="text-sm">({pointsToSpend} points)</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default VoteModal