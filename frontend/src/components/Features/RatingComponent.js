import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import axios from 'axios'

const RatingComponent = ({ feature, userRating, onClose, onSuccess }) => {
  const { session } = useAuth()
  const [activeTab, setActiveTab] = useState('upvote')
  const [starRating, setStarRating] = useState(0)
  const [feedback, setFeedback] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const submitRating = async (ratingType, ratingValue = null) => {
    try {
      setSubmitting(true)
      setError('')
      
      const ratingData = {
        rating_type: ratingType,
        rating_value: ratingValue,
        feedback: feedback.trim() || null
      }

      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/features/${feature.id}/rate`,
        ratingData,
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`
          }
        }
      )

      // Show success message
      alert(`Rating submitted! You earned ${response.data.points_earned} points${response.data.is_daily_first ? ' (including daily bonus!)' : ''}`)
      
      onSuccess()
    } catch (error) {
      console.error('Error submitting rating:', error)
      setError(error.response?.data?.detail || 'Failed to submit rating')
    } finally {
      setSubmitting(false)
    }
  }

  const handleStarSubmit = () => {
    if (starRating > 0) {
      submitRating('star', starRating)
    }
  }

  const handleFeedbackSubmit = () => {
    if (feedback.trim()) {
      submitRating('feedback')
    }
  }

  if (userRating) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Your Rating</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="text-center py-8">
            <div className="text-6xl mb-4">
              {userRating.rating_type === 'upvote' ? '👍' : 
               userRating.rating_type === 'downvote' ? '👎' : 
               userRating.rating_type === 'star' ? '⭐' : '💬'}
            </div>
            <p className="text-gray-600 mb-2">
              You've already rated this feature!
            </p>
            <p className="text-sm text-gray-500">
              You earned {userRating.points_earned} points for this rating
            </p>
            {userRating.feedback && (
              <div className="mt-4 p-3 bg-gray-50 rounded-md text-left">
                <p className="text-sm text-gray-700">{userRating.feedback}</p>
              </div>
            )}
          </div>

          <button
            onClick={onClose}
            className="w-full bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Rate Feature</h3>
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
          <h4 className="font-medium text-gray-900 mb-2">{feature.title}</h4>
          <p className="text-sm text-gray-600">{feature.description}</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex space-x-1 mb-4 border-b">
          <button
            onClick={() => setActiveTab('upvote')}
            className={`px-4 py-2 text-sm font-medium ${activeTab === 'upvote' 
              ? 'text-blue-600 border-b-2 border-blue-600' 
              : 'text-gray-500 hover:text-gray-700'}`}
          >
            👍 Thumbs Up/Down
          </button>
          <button
            onClick={() => setActiveTab('star')}
            className={`px-4 py-2 text-sm font-medium ${activeTab === 'star' 
              ? 'text-blue-600 border-b-2 border-blue-600' 
              : 'text-gray-500 hover:text-gray-700'}`}
          >
            ⭐ Star Rating
          </button>
          <button
            onClick={() => setActiveTab('feedback')}
            className={`px-4 py-2 text-sm font-medium ${activeTab === 'feedback' 
              ? 'text-blue-600 border-b-2 border-blue-600' 
              : 'text-gray-500 hover:text-gray-700'}`}
          >
            💬 Feedback
          </button>
        </div>

        {/* Tab Content */}
        <div className="mb-6">
          {activeTab === 'upvote' && (
            <div className="text-center py-4">
              <p className="text-sm text-gray-600 mb-4">Quick rating - earn 5 points!</p>
              <div className="flex justify-center space-x-4">
                <button
                  onClick={() => submitRating('upvote', 1)}
                  disabled={submitting}
                  className="flex items-center space-x-2 px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  <span className="text-xl">👍</span>
                  <span>Thumbs Up</span>
                </button>
                <button
                  onClick={() => submitRating('downvote', -1)}
                  disabled={submitting}
                  className="flex items-center space-x-2 px-6 py-3 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  <span className="text-xl">👎</span>
                  <span>Thumbs Down</span>
                </button>
              </div>
            </div>
          )}

          {activeTab === 'star' && (
            <div className="text-center py-4">
              <p className="text-sm text-gray-600 mb-4">Rate from 1-5 stars - earn 10 points!</p>
              <div className="flex justify-center space-x-1 mb-4">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setStarRating(star)}
                    className={`text-2xl ${starRating >= star ? 'text-yellow-400' : 'text-gray-300'} hover:text-yellow-400`}
                  >
                    ⭐
                  </button>
                ))}
              </div>
              <button
                onClick={handleStarSubmit}
                disabled={starRating === 0 || submitting}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                Submit {starRating} Star{starRating !== 1 ? 's' : ''}
              </button>
            </div>
          )}

          {activeTab === 'feedback' && (
            <div className="py-4">
              <p className="text-sm text-gray-600 mb-4">Share detailed feedback - earn 15 points!</p>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Share your thoughts about this feature..."
                className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={4}
              />
              <button
                onClick={handleFeedbackSubmit}
                disabled={!feedback.trim() || submitting}
                className="mt-3 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                Submit Feedback
              </button>
            </div>
          )}
        </div>

        {/* Additional Feedback */}
        <div className="border-t pt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Additional Comments (optional - earn bonus points!)
          </label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Any additional thoughts..."
            className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={3}
          />
        </div>
      </div>
    </div>
  )
}

export default RatingComponent