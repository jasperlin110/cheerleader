import "./App.css"
import {KeyboardEvent, useCallback, useEffect, useRef, useState} from "react";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

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

    useEffect(() => {
        userMessageRef.current?.focus();
    });

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

        try {
            const response = await fetch(`${BASE_URL}/chat/bot-response/`, {
                method: "POST",
                credentials: "include",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({role: "user", time: new Date().toLocaleTimeString(), message: userMessage}),
            });

            const reader = response.body!.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let botMessageAdded = false;

            while (true) {
                const {done, value} = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, {stream: true});
                const lines = buffer.split("\n");
                buffer = lines.pop()!;

                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    const data = JSON.parse(line.slice(6));

                    if (data.token) {
                        if (!botMessageAdded) {
                            botMessageAdded = true;
                            setMessageHistory(prev => [...prev, {role: "bot", time: "", message: data.token}]);
                        } else {
                            setMessageHistory(prev => {
                                const updated = [...prev];
                                updated[updated.length - 1] = {
                                    ...updated[updated.length - 1],
                                    message: updated[updated.length - 1].message + data.token,
                                };
                                return updated;
                            });
                        }
                    }

                    if (data.done) {
                        setMessageHistory(prev => {
                            const updated = [...prev];
                            updated[updated.length - 1] = {
                                ...updated[updated.length - 1],
                                time: new Date(data.time).toLocaleTimeString(),
                            };
                            return updated;
                        });
                        setIsBotResponding(false);
                    }
                }
            }
        } catch {
            setIsBotResponding(false);
        }
    }, []);

    const isThinking = isBotResponding &&
        (messageHistory.length === 0 || messageHistory[messageHistory.length - 1].role === "user");

    return (
        <>
            <div className="header">
                <h1 className="header-item header-title">Hire Jasper Lin</h1>
                <a
                    className="header-item social-media"
                    href="https://www.linkedin.com/in/jasperlin110/"
                    target="_blank"
                >
                    linkedin
                </a>
                <a
                    className="header-item social-media"
                    href="https://github.com/jasperlin110/cheerleader"
                    target="_blank"
                >
                    github
                </a>
                <a
                    className="header-item social-media"
                    href="https://drive.google.com/file/d/1ZPBtYsnzcirl_qtCHNa-WRtsUA7g5HgQ/view?usp=sharing"
                    target="_blank"
                >
                    resume
                </a>
            </div>

            <div className="terminal">
                <div className="static-line">Welcome! If you're here, you might be considering hiring Jasper Lin...</div>
                <div className="static-line">...so he hired someone to convince you to do so.</div>
                <div className="static-line"></div>
                <div className="static-line">Just kidding- he built an AI-powered chatbot to convince you.</div>
                <div className="static-line">That's me- Cheerleader.</div>
                <div className="static-line"></div>
                <div className="static-line">You get 3 questions- what do you want to know about Jasper?</div>
                <div className="static-line"></div>
                <div className="static-line">This site is currently in hibernation mode and will take a bit of time to start up.</div>
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
            </div>
        </>
    );
}

export default App;
