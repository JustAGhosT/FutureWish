import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import axios from 'axios'

const RequestForm = ({ onClose, onSuccess }) => {
  const { session } = useAuth()
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'ui_ux',
    request_type: 'feature',
    priority: 'medium',
    use_case: '',
    expected_behavior: '',
    current_workaround: ''
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const categories = [
    { value: 'ui_ux', label: 'UI/UX' },
    { value: 'performance', label: 'Performance' },
    { value: 'integration', label: 'Integration' },
    { value: 'security', label: 'Security' },
    { value: 'mobile', label: 'Mobile' },
    { value: 'api', label: 'API' },
    { value: 'other', label: 'Other' }
  ]

  const requestTypes = [
    { value: 'feature', label: 'New Feature', cost: 25 },
    { value: 'enhancement', label: 'Enhancement', cost: 15 },
    { value: 'bug_fix', label: 'Bug Fix', cost: 10 },
    { value: 'integration', label: 'Integration', cost: 35 }
  ]

  const priorities = [
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' },
    { value: 'critical', label: 'Critical' }
  ]

  const getCurrentCost = () => {
    const selectedType = requestTypes.find(type => type.value === formData.request_type)
    return selectedType ? selectedType.cost : 25
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.title.trim() || !formData.description.trim()) {
      setError('Title and description are required')
      return
    }

    try {
      setSubmitting(true)
      setError('')

      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/requests`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${session?.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      onSuccess(response.data)
      onClose()
    } catch (error) {
      console.error('Error submitting request:', error)
      setError(error.response?.data?.detail || 'Failed to submit request')
    } finally {
      setSubmitting(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Submit Feature Request</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 p-2"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Request Type & Cost */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-blue-900">
                  Request Type
                </label>
                <span className="text-sm font-bold text-blue-600">
                  Cost: {getCurrentCost()} points
                </span>
              </div>
              <select
                name="request_type"
                value={formData.request_type}
                onChange={handleInputChange}
                className="w-full p-2 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {requestTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label} ({type.cost} points)
                  </option>
                ))}
              </select>
            </div>

            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                placeholder="Brief, descriptive title for your request"
                className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                maxLength={200}
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                {formData.title.length}/200 characters
              </p>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description *
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="Detailed description of your feature request"
                className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={4}
                maxLength={2000}
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                {formData.description.length}/2000 characters
              </p>
            </div>

            {/* Category and Priority */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category
                </label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {categories.map(category => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority
                </label>
                <select
                  name="priority"
                  value={formData.priority}
                  onChange={handleInputChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {priorities.map(priority => (
                    <option key={priority.value} value={priority.value}>
                      {priority.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Use Case */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Use Case
              </label>
              <textarea
                name="use_case"
                value={formData.use_case}
                onChange={handleInputChange}
                placeholder="Describe the specific use case for this feature"
                className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={3}
                maxLength={1000}
              />
              <p className="text-xs text-gray-500 mt-1">
                {formData.use_case.length}/1000 characters
              </p>
            </div>

            {/* Expected Behavior */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Expected Behavior
              </label>
              <textarea
                name="expected_behavior"
                value={formData.expected_behavior}
                onChange={handleInputChange}
                placeholder="Describe how this feature should work"
                className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={3}
                maxLength={1000}
              />
              <p className="text-xs text-gray-500 mt-1">
                {formData.expected_behavior.length}/1000 characters
              </p>
            </div>

            {/* Current Workaround */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Current Workaround
              </label>
              <textarea
                name="current_workaround"
                value={formData.current_workaround}
                onChange={handleInputChange}
                placeholder="How do you currently handle this need?"
                className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={3}
                maxLength={1000}
              />
              <p className="text-xs text-gray-500 mt-1">
                {formData.current_workaround.length}/1000 characters
              </p>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {submitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Submitting...</span>
                  </>
                ) : (
                  <>
                    <span>Submit Request</span>
                    <span className="text-sm">({getCurrentCost()} points)</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default RequestForm