import React, { useEffect, useState } from 'react'
import axios from 'axios'

export default function AdminDLQ() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [token, setToken] = useState(localStorage.getItem('ADMIN_API_KEY') || '')
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchItems()
  }, [])

  async function fetchItems() {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get('/admin/dlq?count=100', { headers: token ? { 'X-Admin-Token': token } : {} })
      setItems(res.data.items || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function requeue(index) {
    try {
      await axios.post('/admin/dlq/requeue', { index }, { headers: token ? { 'X-Admin-Token': token } : {} })
      fetchItems()
    } catch (err) {
      setError(err.message)
    }
  }

  async function removeItem(index) {
    try {
      await axios.delete('/admin/dlq', { params: { index }, headers: token ? { 'X-Admin-Token': token } : {} })
      fetchItems()
    } catch (err) {
      setError(err.message)
    }
  }

  function saveToken() {
    localStorage.setItem('ADMIN_API_KEY', token)
    fetchItems()
  }

  return (
    <div>
      <div className="mb-4 flex items-center gap-4">
        <input
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="border px-2 py-1 rounded w-80"
          placeholder="Admin API Key (paste or leave blank if not required)"
        />
        <button className="bg-blue-600 text-white px-3 py-1 rounded" onClick={saveToken}>Save</button>
        <button className="bg-gray-200 px-3 py-1 rounded" onClick={fetchItems}>Refresh</button>
      </div>

      {error && <div className="text-red-600 mb-4">Error: {String(error)}</div>}

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="bg-white shadow-sm rounded-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Payload</th>
                <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white">
              {items.map((i) => (
                <tr key={i.index} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-700">{i.index}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 whitespace-pre-wrap">{JSON.stringify(i.payload, null, 2)}</td>
                  <td className="px-4 py-3 text-sm">
                    <button className="mr-2 bg-green-600 text-white px-2 py-1 rounded" onClick={() => requeue(i.index)}>Requeue</button>
                    <button className="bg-red-600 text-white px-2 py-1 rounded" onClick={() => removeItem(i.index)}>Delete</button>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-sm text-gray-500">No items in DLQ</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
