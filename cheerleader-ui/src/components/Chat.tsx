import { Fragment, KeyboardEvent, RefObject } from "react";

const CHIPS = ["what's he up to now?", "what's he built?", "what does he like to do for fun?"];

export interface ChatMessage {
    role: string;
    time: string;
    message: string;
}

interface ChatProps {
    messageHistory: ChatMessage[];
    isThinking: boolean;
    isBotResponding: boolean;
    remaining: number;
    inputValue: string;
    userMessageRef: RefObject<HTMLInputElement>;
    handleInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    handleKeyDown: (event: KeyboardEvent<HTMLInputElement>) => void;
    handleChipClick: (chip: string) => void;
}

export default function Chat({
    messageHistory,
    isThinking,
    isBotResponding,
    remaining,
    inputValue,
    userMessageRef,
    handleInputChange,
    handleKeyDown,
    handleChipClick,
}: ChatProps) {
    return (
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
    );
}
