import React, { useState } from "react";
import {
  SafeAreaView,
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
} from "react-native";
import { StatusBar } from "expo-status-bar";

const API_BASE_URL = "http://localhost:5000";
const PROCESS_ID_REGEX = /^VISA-\d{6}$/;

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [intent, setIntent] = useState("-");
  const [processIdInput, setProcessIdInput] = useState("");
  const [processInfo, setProcessInfo] = useState(null);
  const [history, setHistory] = useState([]);
  const [messages, setMessages] = useState([
    {
      from: "bot",
      text: "Ola! Sou o assistente YOUVISA. Posso ajudar com status, documentos e prazo.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const loadHistory = async (currentSessionId) => {
    if (!currentSessionId) return;
    try {
      const response = await fetch(`${API_BASE_URL}/history/${currentSessionId}`);
      const data = await response.json();
      if (response.ok) {
        setHistory(Array.isArray(data.logs) ? data.logs : []);
      }
    } catch (error) {
      // Optional UX path: failing to load history should not block chat.
    }
  };

  const sendMessage = async (overrideText) => {
    const text = (overrideText ?? input).trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { from: "user", text }]);
    if (overrideText === undefined) {
      setInput("");
    } else {
      setProcessIdInput("");
    }
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setMessages((prev) => [
          ...prev,
          { from: "bot", text: data.error || "Erro ao processar mensagem." },
        ]);
        return;
      }

      if (data.session_id) {
        setSessionId(data.session_id);
        loadHistory(data.session_id);
      }
      if (data.intent) setIntent(data.intent);

      const replies = Array.isArray(data.responses) ? data.responses : [];
      if (!replies.length) {
        setMessages((prev) => [
          ...prev,
          { from: "bot", text: "Sem resposta do assistente." },
        ]);
        return;
      }

      setMessages((prev) => [
        ...prev,
        ...replies.map((reply) => ({ from: "bot", text: reply })),
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          from: "bot",
          text: "Falha de conexao com o backend. Verifique API_BASE_URL.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const consultProcess = async () => {
    const processId = processIdInput.trim().toUpperCase();
    if (!processId) return;
    if (!PROCESS_ID_REGEX.test(processId)) {
      setProcessInfo(null);
      await sendMessage(processIdInput);
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/process/${processId}`);
      const data = await response.json();
      if (!response.ok) {
        setProcessInfo({ error: data.error || "Processo nao encontrado." });
        return;
      }
      setProcessInfo(data);
    } catch (error) {
      setProcessInfo({ error: "Falha de conexao ao consultar processo." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      <View style={styles.header}>
        <Text style={styles.title}>YOUVISA - Atendimento Inteligente</Text>
        <Text style={styles.meta}>
          Sessao: {sessionId || "nao iniciada"} | Intent atual: {intent}
        </Text>
      </View>

      <View style={styles.processCard}>
        <Text style={styles.sectionTitle}>Consulta rapida de processo</Text>
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            placeholder="Somente codigo (ex: VISA-202401)"
            value={processIdInput}
            onChangeText={setProcessIdInput}
            editable={!loading}
            autoCapitalize="characters"
          />
          <TouchableOpacity style={styles.button} onPress={consultProcess}>
            <Text style={styles.buttonText}>{loading ? "..." : "Consultar"}</Text>
          </TouchableOpacity>
        </View>
        {!!processInfo && (
          <View style={styles.processBox}>
            {"error" in processInfo ? (
              <Text style={styles.errorText}>{processInfo.error}</Text>
            ) : (
              <Text style={styles.processText}>
                {processInfo.process_id}: {processInfo.status}
              </Text>
            )}
          </View>
        )}
      </View>

      <ScrollView style={styles.chat} contentContainerStyle={styles.chatContent}>
        {messages.map((msg, idx) => (
          <View
            key={`${msg.from}-${idx}`}
            style={[
              styles.bubble,
              msg.from === "user" ? styles.userBubble : styles.botBubble,
            ]}
          >
            <Text style={styles.bubbleText}>{msg.text}</Text>
          </View>
        ))}
      </ScrollView>

      <View style={styles.historyCard}>
        <Text style={styles.sectionTitle}>Historico recente</Text>
        {history.slice(0, 3).map((item, index) => (
          <Text style={styles.historyText} key={`${item.created_at}-${index}`}>
            Q: {item.question}
          </Text>
        ))}
      </View>

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          placeholder="Digite sua mensagem"
          value={input}
          onChangeText={setInput}
          editable={!loading}
        />
        <TouchableOpacity style={styles.button} onPress={sendMessage}>
          <Text style={styles.buttonText}>{loading ? "..." : "Enviar"}</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f2f4f8",
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#dde1e6",
    backgroundColor: "#ffffff",
  },
  title: {
    fontSize: 17,
    fontWeight: "800",
    color: "#161616",
  },
  meta: {
    marginTop: 4,
    color: "#525252",
    fontSize: 12,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#161616",
    marginBottom: 6,
  },
  processCard: {
    backgroundColor: "#ffffff",
    margin: 12,
    marginBottom: 0,
    borderWidth: 1,
    borderColor: "#dde1e6",
    borderRadius: 10,
    padding: 10,
  },
  processBox: {
    marginTop: 8,
  },
  processText: {
    color: "#0f62fe",
    fontWeight: "600",
  },
  errorText: {
    color: "#da1e28",
  },
  chat: {
    flex: 1,
  },
  chatContent: {
    padding: 16,
    gap: 10,
  },
  bubble: {
    maxWidth: "82%",
    padding: 10,
    borderRadius: 10,
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: "#0f62fe",
  },
  botBubble: {
    alignSelf: "flex-start",
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#dde1e6",
  },
  bubbleText: {
    color: "#161616",
  },
  historyCard: {
    backgroundColor: "#ffffff",
    borderTopWidth: 1,
    borderTopColor: "#dde1e6",
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  historyText: {
    fontSize: 12,
    color: "#525252",
    marginBottom: 2,
  },
  inputRow: {
    flexDirection: "row",
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: "#dde1e6",
    backgroundColor: "#ffffff",
    gap: 8,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#c1c7cd",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: "#ffffff",
  },
  button: {
    backgroundColor: "#0f62fe",
    borderRadius: 8,
    paddingHorizontal: 14,
    justifyContent: "center",
  },
  buttonText: {
    color: "#ffffff",
    fontWeight: "600",
  },
});
