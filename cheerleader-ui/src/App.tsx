import './App.css'
import {useCallback, useEffect, useRef, useState} from "react";
import axios from "axios";

interface ChatMessage {
    role: string,
    time: string,
    message: string,
}

function App() {
    const [loginTime] = useState<string>(new Date().toTimeString());

    const [messageHistory, setMessageHistory] = useState<ChatMessage[]>([]);
    const userMessageRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        userMessageRef.current?.focus();
    });

    useEffect(() => {
        axios.get("http://localhost:8000/csrf/").then(_ => {});
    }, []);

    const handleKeyDown = useCallback( async (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === "Enter" && userMessageRef.current != null) {
            const userMessageObject: ChatMessage = {
                role: "user",
                time: new Date().toLocaleTimeString(),
                message: userMessageRef.current.value,
            };
            setMessageHistory(previousMessageHistory => [...previousMessageHistory, userMessageObject]);
            userMessageRef.current.value = "";

            const botMessageObject: ChatMessage = await axios.post(
                "http://localhost:8000/chat/bot-response/",
                userMessageObject
            ).then(response => {
                const botMessageObject = response.data;
                botMessageObject.time = new Date(botMessageObject.time).toLocaleTimeString();
                return botMessageObject;
            });
            setMessageHistory(previousMessageHistory => [...previousMessageHistory, botMessageObject]);
        }
    }, []);

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
                <div className="static-line">Just kidding- he built a GPT-powered chatbot to convince you.</div>
                <div className="static-line">That's me- Cheerleader.</div>
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
