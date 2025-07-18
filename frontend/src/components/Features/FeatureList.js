import React, { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import FeatureCard from './FeatureCard'
import axios from 'axios'

const FeatureList = () => {
  const { session } = useAuth()
  const [features, setFeatures] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState({
    category: '',
    status: ''
  })

  useEffect(() => {
    fetchFeatures()
  }, [session, filter])

  const fetchFeatures = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filter.category) params.append('category', filter.category)
      if (filter.status) params.append('status', filter.status)
      
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/features?${params}`,
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`
          }
        }
      )
      setFeatures(response.data)
    } catch (error) {
      console.error('Error fetching features:', error)
      setError('Failed to load features')
    } finally {
      setLoading(false)
    }
  }

  const handleRatingSubmitted = () => {
    // Refresh features after rating
    fetchFeatures()
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
          onClick={fetchFeatures}
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Feature Rating</h1>
        <p className="text-gray-600">
          Rate features to earn points and help shape the future of our platform!
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Category
          </label>
          <select
            value={filter.category}
            onChange={(e) => setFilter({...filter, category: e.target.value})}
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            Status
          </label>
          <select
            value={filter.status}
            onChange={(e) => setFilter({...filter, status: e.target.value})}
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="under_review">Under Review</option>
            <option value="implemented">Implemented</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      {/* Points Info */}
      <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-medium text-blue-900 mb-2">💎 Earn Points</h3>
        <div className="text-sm text-blue-800">
          <p><strong>+5 points</strong> for thumbs up/down • <strong>+10 points</strong> for star ratings • <strong>+15 points</strong> for feedback</p>
          <p><strong>+5 bonus points</strong> for your first rating each day!</p>
        </div>
      </div>

      {/* Feature Grid */}
      {features.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg">No features found</div>
          <p className="text-gray-400 mt-2">Try adjusting your filters</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <FeatureCard
              key={feature.id}
              feature={feature}
              onRatingSubmitted={handleRatingSubmitted}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default FeatureList