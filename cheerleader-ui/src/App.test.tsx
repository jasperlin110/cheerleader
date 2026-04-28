import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function historyResponse(messages: Array<{ role: string; time: string; message: string }> = []) {
    return {
        ok: true,
        json: async () => ({ messages }),
    }
}

beforeEach(() => {
    mockFetch.mockReset()
    mockFetch.mockResolvedValue(historyResponse())
})

describe('App', () => {
    it('renders the terminal header', async () => {
        render(<App />)
        expect(screen.getByText(/jasperlin\.sh/)).toBeInTheDocument()
    })

    it('renders nav links', () => {
        render(<App />)
        expect(screen.getByRole('link', { name: /linkedin/i })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: /github/i })).toBeInTheDocument()
        expect(screen.getByRole('link', { name: /resume/i })).toBeInTheDocument()
    })

    it('fetches history on mount with credentials', async () => {
        render(<App />)
        await waitFor(() => expect(mockFetch).toHaveBeenCalledOnce())
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining('/chat/history/'),
            expect.objectContaining({ credentials: 'include' }),
        )
    })

    it('shows max questions remaining on fresh session', async () => {
        render(<App />)
        await waitFor(() =>
            expect(document.body).toHaveTextContent('3 questions remaining')
        )
    })

    it('restores message history from session', async () => {
        mockFetch.mockResolvedValue(historyResponse([
            { role: 'user', time: '2024-01-01T00:00:00Z', message: 'Tell me about yourself' },
            { role: 'bot',  time: '2024-01-01T00:00:01Z', message: 'I am Jasper.' },
        ]))
        render(<App />)
        await waitFor(() => {
            expect(screen.getByText('Tell me about yourself')).toBeInTheDocument()
            expect(screen.getByText('I am Jasper.')).toBeInTheDocument()
        })
    })

    it('decrements remaining count based on restored history', async () => {
        const messages = [
            { role: 'user', time: '', message: 'Q1' },
            { role: 'bot',  time: '', message: 'A1' },
        ]
        mockFetch.mockResolvedValue(historyResponse(messages))
        render(<App />)
        await waitFor(() =>
            expect(document.body).toHaveTextContent('2 questions remaining')
        )
    })

    it('shows done message when 0 questions remain', async () => {
        const messages = Array.from({ length: 3 }, (_, i) => ([
            { role: 'user', time: '', message: `Q${i}` },
            { role: 'bot',  time: '', message: `A${i}` },
        ])).flat()
        mockFetch.mockResolvedValue(historyResponse(messages))
        render(<App />)
        await waitFor(() =>
            expect(screen.getByText(/0 questions remaining — thanks for stopping by/i)).toBeInTheDocument()
        )
    })

    it('shows suggestion chips when idle with questions remaining', async () => {
        render(<App />)
        await waitFor(() =>
            expect(screen.getByText(/what's he up to now\?/)).toBeInTheDocument()
        )
        expect(screen.getByText(/what's he built\?/)).toBeInTheDocument()
        expect(screen.getByText(/what does he like to do for fun\?/)).toBeInTheDocument()
    })

    it('clicking a chip populates the input', async () => {
        const user = userEvent.setup()
        render(<App />)
        await waitFor(() => screen.getByText(/what's he built\?/))
        await user.click(screen.getByText(/what's he built\?/))
        expect(screen.getByRole('textbox')).toHaveValue("what's he built?")
    })

    it('hides chips while bot is responding', async () => {
        mockFetch
            .mockResolvedValueOnce(historyResponse())
            .mockImplementationOnce(() => new Promise(() => {})) // never resolves
        render(<App />)

        await waitFor(() => screen.getByRole('textbox'))
        const input = screen.getByRole('textbox')
        await userEvent.type(input, 'hello{Enter}')

        await waitFor(() =>
            expect(screen.queryByText(/what's he built\?/)).not.toBeInTheDocument()
        )
    })

    it('sends correct JSON payload on submit', async () => {
        mockFetch
            .mockResolvedValueOnce(historyResponse())
            .mockImplementationOnce(() => new Promise(() => {}))
        render(<App />)

        await waitFor(() => screen.getByRole('textbox'))
        await userEvent.type(screen.getByRole('textbox'), 'hello world{Enter}')

        await waitFor(() =>
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/chat/bot-response/'),
                expect.objectContaining({
                    method: 'POST',
                    credentials: 'include',
                    body: expect.stringContaining('"message":"hello world"'),
                }),
            )
        )
    })

    it('does not submit on empty input', async () => {
        render(<App />)
        await waitFor(() => screen.getByRole('textbox'))
        await userEvent.type(screen.getByRole('textbox'), '{Enter}')
        expect(mockFetch).toHaveBeenCalledTimes(1) // only the history fetch
    })
})
