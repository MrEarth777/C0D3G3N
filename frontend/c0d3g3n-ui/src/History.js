import React, { useState, useEffect } from "react";

function History() {
    const [history, setHistory] = useState([]);

    useEffect(() => {
        fetch("http://127.0.0.1:8000/history/")
            .then(response => response.json())
            .then(data => setHistory(data));
    }, []);

    return (
        <div>
            <h2>Conversiegeschiedenis</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Legacy Code</th>
                        <th>Van</th>
                        <th>Naar</th>
                        <th>Download</th>
                    </tr>
                </thead>
                <tbody>
                    {history.map((conv) => (
                        <tr key={conv.id}>
                            <td>{conv.id}</td>
                            <td><pre>{conv.legacy_code.slice(0, 30)}...</pre></td>
                            <td>{conv.source_language}</td>
                            <td>{conv.target_language}</td>
                            <td>
                                <a href={`http://127.0.0.1:8000/download/${conv.id}`} download>
                                    Download
                                </a>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default History;
