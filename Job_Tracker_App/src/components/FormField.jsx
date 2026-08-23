export default function FormField({ label, required, error, children }) {
  return (
    <div className="space-y-1.5">
      <label className="flex items-center gap-1 text-sm font-medium text-gray-300">
        {label}
        {required && <span className="text-red-400 text-xs" aria-hidden="true">*</span>}
      </label>
      {children}
      {error && (
        <p className="text-xs text-red-400 flex items-center gap-1" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
