// DocumentList.jsx
export default function DocumentList({ docs = [], onSelect, selectedDoc }) {
  return (
    <div style={{ marginTop: 20 }}>
      <h3>Uploaded Documents</h3>
      <ul>
        {docs.length > 0 ? (
          docs.map((doc) => (
            <li key={doc} style={{ marginBottom: 8 }}>
              <button
                onClick={() => onSelect(doc)}
                style={{
                  padding: "6px 12px",
                  backgroundColor: selectedDoc === doc ? "#4caf50" : "#eee",
                  color: selectedDoc === doc ? "#fff" : "#000",
                  border: "none",
                  borderRadius: 4,
                  cursor: "pointer",
                }}
              >
                {doc} {selectedDoc === doc ? "(Selected)" : ""}
              </button>
            </li>
          ))
        ) : (
          <li>No documents uploaded</li>
        )}
      </ul>
    </div>
  );
}
