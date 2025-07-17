import React from 'react'
import { useAuth } from '../../contexts/AuthContext'

const Navbar = () => {
  const { user, userProfile, signOut } = useAuth()

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-2xl font-bold text-blue-600">EngageMesh</h1>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {userProfile && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-700">
                  {userProfile.points} points
                </span>
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              </div>
            )}
            
            <div className="flex items-center space-x-3">
              {user?.user_metadata?.avatar_url && (
                <img
                  src={user.user_metadata.avatar_url}
                  alt="Profile"
                  className="w-8 h-8 rounded-full"
                />
              )}
              <span className="text-sm text-gray-700">
                {user?.user_metadata?.name || userProfile?.name || user?.email}
              </span>
              <button
                onClick={signOut}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar