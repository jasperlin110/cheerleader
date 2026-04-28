import "./App.css";
import { Fragment, KeyboardEvent, useCallback, useEffect, useRef, useState } from "react";

const BASE_URL     = import.meta.env.VITE_API_URL     ?? "http://localhost:8000";
const LINKEDIN_URL = import.meta.env.VITE_LINKEDIN_URL ?? "https://www.linkedin.com/in/jasperlin110/";
const GITHUB_URL   = import.meta.env.VITE_GITHUB_URL   ?? "https://github.com/jasperlin110/cheerleader";
const RESUME_URL   = import.meta.env.VITE_RESUME_URL   ?? "https://drive.google.com/file/d/1ptXrV8il4yFkWTXGcKfMJKBhIjI_eNFn/view?usp=sharing";

const CHARS_PER_SECOND = 350;
const MAX_QUESTIONS = 10;

const CHIPS = ["what're you looking for?", "what're you up to now?", "what's your tech stack?"];

const ASCII_HEADER = String.raw`     _    _    ____  ____  _____ ____    _     ___ _   _
    | |  / \  / ___||  _ \| ____|  _ \  | |   |_ _| \ | |
 _  | | / _ \ \___ \| |_) |  _| | |_) | | |    | ||  \| |
| |_| |/ ___ \ ___) |  __/| |___|  _ <  | |___ | || |\  |
 \___//_/   \_\____/|_|   |_____|_| \_\ |_____|___|_| \_|`;

interface ChatMessage {
    role: string;
    time: string;
    message: string;
}

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
                        <a href={RESUME_URL}   target="_blank" rel="noopener" className="resume-link">resume ↗</a>
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
                    <div className="convo">
                        <div className="prompt-row">
                            <span className="prompt-dollar">$</span>
                            <span className="prompt-cmd">whoami</span>
                        </div>
                        <div className="whoami-resp">
                            jasper lin — software engineer · b.a. computer science, uc berkeley (december 2020)
                        </div>

                        {messageHistory.map((msg, i) => {
                            if (msg.role !== "user") return null;
                            const botMsg = messageHistory[i + 1]?.role === "bot"
                                ? messageHistory[i + 1]
                                : null;
                            return (
                                <Fragment key={i}>
                                    <div className="prompt-row">
                                        <span className="prompt-dollar">$</span>
                                        <span className="prompt-cmd">
                                            cheerleader --ask &ldquo;{msg.message}&rdquo;
                                        </span>
                                    </div>
                                    <div className="exchange">
                                        <div>
                                            <div className="msg-meta msg-meta-user">you{msg.time ? ` · ${msg.time}` : ""}</div>
                                            <div className="msg-body-user">{msg.message}</div>
                                        </div>
                                        {botMsg && (
                                            <div>
                                                <div className="msg-meta msg-meta-bot">
                                                    cheerleader{botMsg.time ? ` · ${botMsg.time}` : ""}
                                                </div>
                                                <div className="msg-body-bot">{botMsg.message}</div>
                                            </div>
                                        )}
                                    </div>
                                </Fragment>
                            );
                        })}

                        {isThinking ? (
                            <div className="thinking-line">cheerleader is thinking</div>
                        ) : remaining > 0 && !isBotResponding ? (
                            <>
                                <div
                                    className="prompt-input-row"
                                    onClick={() => userMessageRef.current?.focus()}
                                >
                                    <span className="prompt-dollar">$</span>
                                    <span className="prompt-ask">ask&gt; </span>
                                    <span className="prompt-user-text">{inputValue}</span>
                                    <span className="cursor-blink" />
                                    <input
                                        className="prompt-input-hidden"
                                        ref={userMessageRef}
                                        type="text"
                                        value={inputValue}
                                        onChange={handleInputChange}
                                        onKeyDown={handleKeyDown}
                                        autoComplete="off"
                                        autoCapitalize="off"
                                        spellCheck={false}
                                    />
                                </div>
                                <div className="chips">
                                    {CHIPS.map(chip => (
                                        <button
                                            key={chip}
                                            className="chip"
                                            onClick={() => handleChipClick(chip)}
                                        >
                                            ⬡ {chip}
                                        </button>
                                    ))}
                                </div>
                            </>
                        ) : remaining === 0 && !isBotResponding ? (
                            <div className="done-line">
                                [ <span className="boot-note">done</span> ] 0 questions remaining — thanks for stopping by
                            </div>
                        ) : null}
                    </div>

                    <div className="spacer" />

                    {/* ── Status bar ── */}
                    <div className="status-bar">
                        <span>
                            questions <CounterDots remaining={remaining} /> · {MAX_QUESTIONS - remaining}/{MAX_QUESTIONS} used
                        </span>
                        <span className="status-center">⌃↑ history · ⌘K palette · ? help</span>
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
