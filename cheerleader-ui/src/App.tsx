import "./App.css"
import {KeyboardEvent, useCallback, useEffect, useRef, useState} from "react";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const LINKEDIN_URL = import.meta.env.VITE_LINKEDIN_URL ?? "https://www.linkedin.com/in/jasperlin110/";
const GITHUB_URL = import.meta.env.VITE_GITHUB_URL ?? "https://github.com/jasperlin110/cheerleader";
const RESUME_URL = import.meta.env.VITE_RESUME_URL ?? "https://drive.google.com/file/d/1ptXrV8il4yFkWTXGcKfMJKBhIjI_eNFn/view?usp=sharing";

const CHARS_PER_SECOND = 350;

interface ChatMessage {
    role: string,
    time: string,
    message: string,
}

function App() {
    const [loginTime] = useState<string>(new Date().toTimeString());
    const [isBotResponding, setIsBotResponding] = useState<boolean>(false);
    const [messageHistory, setMessageHistory] = useState<ChatMessage[]>([]);
    const userMessageRef = useRef<HTMLInputElement>(null);
    const charQueueRef = useRef<string>("");
    const rafRef = useRef<number | null>(null);
    const pendingDoneTimeRef = useRef<string | null>(null);
    const lastRafTimeRef = useRef<number>(0);

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
                    updated[updated.length - 1] = {...last, message: last.message + chars};
                } else {
                    updated.push({role: "bot", time: "", message: chars});
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
        if (event.key !== "Enter" || userMessageRef.current == null) return;

        const userMessage = userMessageRef.current.value;
        userMessageRef.current.value = "";

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
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({role: "user", time: new Date().toLocaleTimeString(), message: userMessage}),
            });

            if (!response.body) throw new Error("No response body");
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            for (;;) {
                const {done, value} = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, {stream: true});
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

    const isThinking = isBotResponding &&
        (messageHistory.length === 0 || messageHistory[messageHistory.length - 1].role === "user");

    return (
        <>
            <div className="header">
                <h1 className="header-item header-title">Hire Jasper Lin</h1>
                <a className="header-item social-media" href={LINKEDIN_URL} target="_blank">linkedin</a>
                <a className="header-item social-media" href={GITHUB_URL} target="_blank">github</a>
                <a className="header-item social-media" href={RESUME_URL} target="_blank">resume</a>
            </div>

            <div className="terminal">
                <div className="static-line">Welcome! If you're here, you might be considering hiring Jasper Lin.</div>
                <div className="static-line">Meet Cheerleader- an AI-powered chatbot he built to answer your questions about him!</div>
                <div className="static-line"></div>
                <div className="static-line">You get 3 questions- what do you want to know about Jasper?</div>
                <div className="input-line login-line">Logged in @ {loginTime}</div>
                <div className="message-history">
                    {messageHistory.map((message, index) => (
                        <div className="input-line" key={index}>
                            <p className="message-prefix">
                                {message.role === "bot" ? "Cheerleader" : "You"}@ {message.time}:
                            </p>
                            <span className="user-input">
                                {message.message}
                            </span>
                        </div>
                    ))}
                </div>
                {isThinking ? (
                    <div className="thinking-line">
                        Cheerleader is thinking
                    </div>
                ) : !isBotResponding ? (
                    <div className="input-line">
                        <label className="message-prefix" htmlFor="user-input">You:</label>
                        <input
                            className="user-input"
                            id="user-input"
                            ref={userMessageRef}
                            type="text"
                            onKeyDown={handleKeyDown}
                        />
                    </div>
                ) : null}
            </div>
            <div className="disclaimer">
                <p>
                    Although efforts have been made to prevent it, Cheerleader may occasionally generate incorrect information.
                </p>
                <p>Last updated {__BUILD_DATE__}</p>
            </div>
        </>
    );
}

export default App;
