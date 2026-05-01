import "./App.css";
import { KeyboardEvent, useCallback, useEffect, useRef, useState } from "react";
import Chat, { ChatMessage } from "./components/Chat";

const BASE_URL     = import.meta.env.VITE_API_URL      ?? "http://localhost:8000";
const LINKEDIN_URL = import.meta.env.VITE_LINKEDIN_URL ?? "https://www.linkedin.com/in/jasperlin110/";
const GITHUB_URL   = import.meta.env.VITE_GITHUB_URL   ?? "https://github.com/jasperlin110/cheerleader";
const CALENDLY_URL = import.meta.env.VITE_CALENDLY_URL ?? "https://calendly.com/jasper-lin-110/30min";
const RESUME_URL   = import.meta.env.VITE_RESUME_URL;

const CHARS_PER_SECOND = 350;
const MAX_QUESTIONS = 3;

const ASCII_HEADER = String.raw`     _    _    ____  ____  _____ ____    _     ___ _   _
    | |  / \  / ___||  _ \| ____|  _ \  | |   |_ _| \ | |
 _  | | / _ \ \___ \| |_) |  _| | |_) | | |    | ||  \| |
| |_| |/ ___ \ ___) |  __/| |___|  _ <  | |___ | || |\  |
 \___//_/   \_\____/|_|   |_____|_| \_\ |_____|___|_| \_|`;

function CounterDots({ remaining }: { remaining: number }) {
    const filled = "●".repeat(remaining);
    const empty  = "○".repeat(MAX_QUESTIONS - remaining);
    return <span className="counter-dots">{filled}{empty}</span>;
}

function formatLoginTime(): string {
    const now = new Date();
    const time = now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
    const parts = now.toLocaleTimeString("en-US", { timeZoneName: "short" }).split(" ");
    const tz = parts[parts.length - 1] ?? "";
    return `${time} ${tz}`;
}

function App() {
    const [loginTime] = useState<string>(formatLoginTime);
    // We only want to display the Calendly button if the script loads successfully to avoid displaying a broken button
    const [isCalendlyReady, setIsCalendlyReady] = useState<boolean>(false);
    const [isBotResponding, setIsBotResponding] = useState<boolean>(false);
    const [messageHistory, setMessageHistory] = useState<ChatMessage[]>([]);
    const [inputValue, setInputValue] = useState<string>("");
    const userMessageRef = useRef<HTMLInputElement>(null);
    const inputValueRef  = useRef<string>("");
    const charQueueRef   = useRef<string>("");
    const rafRef         = useRef<number | null>(null);
    const pendingDoneTimeRef = useRef<string | null>(null);
    const lastRafTimeRef     = useRef<number>(0);

    useEffect(() => {
        const script = document.createElement("script");
        script.src = "https://assets.calendly.com/assets/external/widget.js";
        script.type = "text/javascript";
        script.onload = () => setIsCalendlyReady(true);
        document.body.appendChild(script);
    }, []);

    useEffect(() => {
        const handleMessage = (e: MessageEvent) => {
            if (e.data?.event === "calendly.event_scheduled") {
                const inviteeUri = e.data.payload?.invitee?.uri;
                fetch(`${BASE_URL}/meeting/`, {
                    method: "POST",
                    credentials: "include",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ invitee_uri: inviteeUri }),
                });
            }
        };
        window.addEventListener("message", handleMessage);
        return () => window.removeEventListener("message", handleMessage);
    }, []);

    useEffect(() => {
        fetch(`${BASE_URL}/chat/history/`, { credentials: "include" })
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (data?.messages?.length) {
                    setMessageHistory(data.messages.map((m: ChatMessage) => ({
                        ...m,
                        time: m.time ? new Date(m.time).toLocaleTimeString() : "",
                    })));
                }
            })
            .catch(() => undefined);
    }, []);

    useEffect(() => {
        userMessageRef.current?.focus();
    });

    useEffect(() => {
        return () => {
            if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
        };
    }, []);

    const drainQueue = useCallback((timestamp: number) => {
        const elapsed = timestamp - lastRafTimeRef.current;
        lastRafTimeRef.current = timestamp;

        if (charQueueRef.current.length > 0) {
            const count = Math.max(1, Math.round(elapsed * CHARS_PER_SECOND / 1000));
            const chars = charQueueRef.current.slice(0, count);
            charQueueRef.current = charQueueRef.current.slice(count);
            setMessageHistory(prev => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                if (last?.role === "bot" && last.time === "") {
                    updated[updated.length - 1] = { ...last, message: last.message + chars };
                } else {
                    updated.push({ role: "bot", time: "", message: chars });
                }
                return updated;
            });
            rafRef.current = requestAnimationFrame(drainQueue);
        } else if (pendingDoneTimeRef.current !== null) {
            rafRef.current = null;
            const time = pendingDoneTimeRef.current;
            pendingDoneTimeRef.current = null;
            setMessageHistory(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    time: new Date(time).toLocaleTimeString(),
                };
                return updated;
            });
            setIsBotResponding(false);
        } else {
            rafRef.current = requestAnimationFrame(drainQueue);
        }
    }, []);

    const startDraining = useCallback(() => {
        if (rafRef.current !== null) return;
        lastRafTimeRef.current = performance.now();
        rafRef.current = requestAnimationFrame(drainQueue);
    }, [drainQueue]);

    const handleKeyDown = useCallback(async (event: KeyboardEvent<HTMLInputElement>) => {
        if (event.key !== "Enter") return;
        const userMessage = inputValueRef.current.trim();
        if (!userMessage) return;

        inputValueRef.current = "";
        setInputValue("");

        setMessageHistory(prev => [...prev, {
            role: "user",
            time: new Date().toLocaleTimeString(),
            message: userMessage,
        }]);
        setIsBotResponding(true);
        charQueueRef.current = "";
        pendingDoneTimeRef.current = null;

        try {
            const response = await fetch(`${BASE_URL}/chat/bot-response/`, {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ role: "user", time: new Date().toLocaleTimeString(), message: userMessage }),
            });

            if (!response.body) throw new Error("No response body");
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            for (;;) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() ?? "";

                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    const data = JSON.parse(line.slice(6));

                    if (data.token) {
                        charQueueRef.current += data.token;
                        startDraining();
                    }

                    if (data.done) {
                        pendingDoneTimeRef.current = data.time;
                    }
                }
            }
        } catch {
            charQueueRef.current = "";
            pendingDoneTimeRef.current = null;
            if (rafRef.current !== null) {
                cancelAnimationFrame(rafRef.current);
                rafRef.current = null;
            }
            setIsBotResponding(false);
        }
    }, [startDraining]);

    const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        inputValueRef.current = e.target.value;
        setInputValue(e.target.value);
    }, []);

    const handleChipClick = useCallback((chip: string) => {
        inputValueRef.current = chip;
        setInputValue(chip);
        userMessageRef.current?.focus();
    }, []);

    const isThinking = isBotResponding &&
        (messageHistory.length === 0 || messageHistory[messageHistory.length - 1].role === "user");

    const userCount = messageHistory.filter(m => m.role === "user").length;
    const remaining = Math.max(0, MAX_QUESTIONS - userCount);

    return (
        <>
            <div className="page-wrap">
                {/* ── Top bar ── */}
                <header className="top-bar">
                    <div className="top-bar-left">
                        <div className="top-bar-logo">
                            <span className="top-bar-dot" />
                            jasperlin.sh
                        </div>
                        <span className="top-bar-sep">·</span>
                        <span className="top-bar-location">austin, tx · {loginTime}</span>
                    </div>
                    <nav className="top-bar-links">
                        <a href={LINKEDIN_URL} target="_blank" rel="noopener">linkedin ↗</a>
                        <a href={GITHUB_URL}   target="_blank" rel="noopener">github ↗</a>
                        {RESUME_URL && <a href={RESUME_URL}   target="_blank" rel="noopener">resume ↗</a>}
                    </nav>
                </header>

                {/* ── Terminal panel ── */}
                <main className="terminal-panel">
                    <pre className="ascii-header">{ASCII_HEADER}</pre>
                    <div className="tagline">software engineer · austin, tx</div>

                    <hr className="sep" />

                    <div className="boot-lines">
                        <div>
                            [ <span className="boot-ok">ok</span> ] mounting{" "}
                            <span className="boot-file">about.md</span>{" · "}
                            <span className="boot-file">experience.json</span>{" · "}
                            <span className="boot-file">skills.ts</span>
                        </div>
                        <div>[ <span className="boot-ok">ok</span> ] cheerleader.agent ready (claude-haiku-4-5)</div>
                        <div>
                            [ <span className="boot-note">note</span> ] you have{" "}
                            <CounterDots remaining={remaining} />{" "}
                            {remaining} question{remaining !== 1 ? "s" : ""} remaining
                        </div>
                    </div>

                    <hr className="sep" />

                    {/* ── Conversation ── */}
                    <Chat
                        messageHistory={messageHistory}
                        isThinking={isThinking}
                        isBotResponding={isBotResponding}
                        isCalendlyReady={isCalendlyReady}
                        remaining={remaining}
                        inputValue={inputValue}
                        calendlyURL={CALENDLY_URL}
                        userMessageRef={userMessageRef}
                        handleInputChange={handleInputChange}
                        handleKeyDown={handleKeyDown}
                        handleChipClick={handleChipClick}
                    />

                    <div className="spacer" />

                    {/* ── Status bar ── */}
                    <div className="status-bar">
                        <span>
                            questions <CounterDots remaining={remaining} /> · {MAX_QUESTIONS - remaining}/{MAX_QUESTIONS} used
                        </span>
                        {isCalendlyReady && (
                            <a
                                href="#"
                                className="action-item"
                                onClick={(e) => {
                                    e.preventDefault();
                                    (window as { Calendly?: { initPopupWidget: (opts: object) => void } }).Calendly?.initPopupWidget({
                                        url: CALENDLY_URL,
                                    });
                                }}
                            >Schedule time with Jasper ↗</a>
                        )}
                        <span>~/cheerleader · main</span>
                    </div>
                </main>

                {/* ── Disclaimer ── */}
                <div className="disclaimer">
                    <p>Although efforts have been made to prevent it, Cheerleader may occasionally generate incorrect information.</p>
                    <p>Last updated {__BUILD_DATE__}</p>
                </div>
            </div>

            <div className="overlay-scanlines" aria-hidden="true" />
            <div className="overlay-vignette" aria-hidden="true" />
        </>
    );
}

export default App;
