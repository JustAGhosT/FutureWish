import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import RatingComponent from './RatingComponent'
import axios from 'axios'

const FeatureCard = ({ feature, onRatingSubmitted }) => {
  const { session } = useAuth()
  const [showRatingModal, setShowRatingModal] = useState(false)
  const [userRating, setUserRating] = useState(null)
  const [loading, setLoading] = useState(false)

  const getCategoryColor = (category) => {
    const colors = {
      'ui_ux': 'bg-blue-100 text-blue-800',
      'performance': 'bg-green-100 text-green-800',
      'integration': 'bg-purple-100 text-purple-800',
      'security': 'bg-red-100 text-red-800',
      'mobile': 'bg-yellow-100 text-yellow-800',
      'api': 'bg-indigo-100 text-indigo-800',
      'other': 'bg-gray-100 text-gray-800'
    }
    return colors[category] || colors.other
  }

  const getStatusColor = (status) => {
    const colors = {
      'active': 'bg-green-100 text-green-800',
      'under_review': 'bg-yellow-100 text-yellow-800',
      'implemented': 'bg-blue-100 text-blue-800',
      'archived': 'bg-gray-100 text-gray-800'
    }
    return colors[status] || colors.active
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

  const checkUserRating = async () => {
    try {
      setLoading(true)
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/features/${feature.id}`,
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`
          }
        }
      )
      setUserRating(response.data.user_rating)
      setShowRatingModal(true)
    } catch (error) {
      console.error('Error checking user rating:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRatingSuccess = () => {
    setShowRatingModal(false)
    onRatingSubmitted()
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200">
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600 text-sm mb-3 line-clamp-3">
                {feature.description}
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between mb-4">
            <div className="flex space-x-2">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(feature.category)}`}>
                {formatCategory(feature.category)}
              </span>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(feature.status)}`}>
                {formatStatus(feature.status)}
              </span>
            </div>
          </div>

          {/* Rating Stats */}
          <div className="flex items-center justify-between mb-4 text-sm text-gray-600">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1">
                <span className="text-green-600">👍</span>
                <span>{feature.upvotes}</span>
              </div>
              <div className="flex items-center space-x-1">
                <span className="text-red-600">👎</span>
                <span>{feature.downvotes}</span>
              </div>
              {feature.average_star_rating > 0 && (
                <div className="flex items-center space-x-1">
                  <span className="text-yellow-500">⭐</span>
                  <span>{feature.average_star_rating.toFixed(1)}</span>
                </div>
              )}
            </div>
            <div className="text-xs text-gray-500">
              {feature.total_ratings} ratings
            </div>
          </div>

          {/* Rate Button */}
          <button
            onClick={checkUserRating}
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Loading...' : 'Rate This Feature'}
          </button>
        </div>
      </div>

      {/* Rating Modal */}
      {showRatingModal && (
        <RatingComponent
          feature={feature}
          userRating={userRating}
          onClose={() => setShowRatingModal(false)}
          onSuccess={handleRatingSuccess}
        />
      )}
    </>
  )
}

export default FeatureCard