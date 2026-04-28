import '@testing-library/jest-dom'
import { vi } from 'vitest'

// @vitejs/plugin-react checks for this at runtime; in jsdom there's no HTML preamble
Object.defineProperty(window, '__vite_plugin_react_preamble_installed__', { value: true })

let frameId = 0
vi.stubGlobal('requestAnimationFrame', (_cb: FrameRequestCallback) => ++frameId)
vi.stubGlobal('cancelAnimationFrame', () => {})
