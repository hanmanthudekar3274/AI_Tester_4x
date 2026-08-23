import { Compass } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="shrink-0 border-t border-gray-800/60 bg-gray-900 px-6 py-2">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-1.5 text-gray-700">
          <Compass size={11} strokeWidth={1.5} />
          <span className="text-xs">JobFlow — local-first, always private</span>
        </div>
        <span className="text-xs text-gray-800 hidden sm:block">Data stored in your browser — never sent anywhere</span>
      </div>
    </footer>
  )
}
