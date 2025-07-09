import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

interface ReportSection {
  subtask_title: string;
  result: any;
}

function App() {
  const [requestText, setRequestText] = useState('');
  const [history, setHistory] = useState<ReportSection[]>([]);
  const [assembledReport, setAssembledReport] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/generate-report', {
        request_text: requestText
      });

      setHistory(response.data.report_sections);
      setAssembledReport(response.data.assembled_report);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setRequestText('');
    setHistory([]);
    setAssembledReport('');
  };

  return (
    <div className="app-container">
      <header>
        <h1>LLM Report Generator</h1>
      </header>
      
      <section className="input-section">
        <textarea
          value={requestText}
          onChange={(e) => setRequestText(e.target.value)}
          placeholder="Enter your request for Manager #1..."
          rows={5}
        />
        <div className="button-row">
          <button onClick={handleSubmit} disabled={loading || !requestText.trim()}>
            {loading ? 'Generating...' : 'Submit'}
          </button>
          <button onClick={handleClear}>Clean Up</button>
        </div>
      </section>

      <section className="history-section">
        <h2>Conversation History</h2>
        {history.length === 0 && <p>No history yet.</p>}
        {history.map((step, index) => (
          <div key={index} className="history-item">
            <h3>{step.subtask_title}</h3>
            <pre>{JSON.stringify(step.result, null, 2)}</pre>
          </div>
        ))}
      </section>

      <section className="assembled-report">
        <h2>Assembled Report</h2>
        <pre>{assembledReport}</pre>
      </section>
    </div>
  );
}

export default App;
