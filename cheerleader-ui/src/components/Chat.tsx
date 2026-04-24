// import useWebSocket, {ReadyState} from "react-use-websocket";
// import {useCallback, useRef, useState} from "react";
//
// interface ChatMessage {
//     type: string,
//     data: string,
// }
//
// function Chat() {
//     const [messageHistory, setMessageHistory] = useState<ChatMessage[]>([]);
//     const userMessageRef = useRef<HTMLInputElement>(null);
//
//     const { sendJsonMessage, readyState } = useWebSocket(
//         "ws://localhost:8000/ws/chat/",
//         {
//             onMessage: (event: MessageEvent) => {
//                 const messageObject = JSON.parse(event.data);
//                 if (messageObject.type === "bot_message") {
//                     setMessageHistory([...messageHistory, messageObject]);
//                 }
//             },
//         }
//     );
//
//     const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLInputElement>) => {
//         if (event.key === "Enter" && userMessageRef.current != null) {
//             const userMessageObject: ChatMessage = {
//                 type: "chat_message",
//                 data: userMessageRef.current.value,
//             };
//             sendJsonMessage(userMessageObject);
//             setMessageHistory([...messageHistory, userMessageObject])
//             userMessageRef.current.value = "";
//         }
//     }, [messageHistory, sendJsonMessage, setMessageHistory]);
//
//     return (
//         <>
//             <div>
//                 {messageHistory.map((message, index) => (
//                     <p key={index}>
//                         {message.type === "bot_message" ? "Cheerleader" : "You"}: {message.data}
//                     </p>
//                 ))}
//             </div>
//
//         </>
//     );
// }
//
// export default Chat;
