import React, { useState, useEffect } from 'react';
import axios from 'axios';

const YourComponent = () => {
  const [notionKey, setNotionKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [createTemplate, setCreateTemplate] = useState(false);
  const [databaseId, setDatabaseId] = useState('');
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [generatedPosts, setGeneratedPosts] = useState([]);
  const [submittedData, setSubmittedData] = useState(null);

  useEffect(() => {
    if (createTemplate) {
      axios.get('http://localhost:8000/get_templates')
        .then(response => setTemplates(response.data))
        .catch(error => console.error('Error fetching templates:', error));
    }
  }, [createTemplate]);

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      if (createTemplate) {
        // Send data to create template endpoint
        const response = await axios.post('http://localhost:8000/create_template', {
          notionKey: notionKey,
          openaiKey: openaiKey,
          text: submittedData,
        });

        setSubmittedData(response.data); // Update state with the created template
      } else {
        // Send data to generate posts endpoint
        const response = await axios.post('http://localhost:8000/generate_posts', {
          notionKey: notionKey,
          openaiKey: openaiKey,
          databaseId: databaseId,
          templateId: selectedTemplate,
        });

        setGeneratedPosts(response.data); // Update state with the generated posts
      }
    } catch (error) {
      console.error('Error submitting data:', error);
    }
  };

  return (
    <div style={{ display: 'flex' }}>
      {/* Left Part - Form */}
      <div style={{ flex: '1', padding: '20px' }}>
        <form onSubmit={handleSubmit}>
          {/* Notion and OpenAI Key Inputs */}
          <label>
            Notion Key:
            <input type="text" value={notionKey} onChange={(e) => setNotionKey(e.target.value)} />
          </label>
          <br />
          <label>
            OpenAI Key:
            <input type="text" value={openaiKey} onChange={(e) => setOpenaiKey(e.target.value)} />
          </label>
          <br />

          {/* Radio Buttons for Create Template or Create Posts from Template */}
          <label>
            <input
              type="radio"
              name="operation"
              value="createTemplate"
              checked={createTemplate}
              onChange={() => setCreateTemplate(true)}
            />
            Create Template
          </label>
          <label>
            <input
              type="radio"
              name="operation"
              value="createPosts"
              checked={!createTemplate}
              onChange={() => setCreateTemplate(false)}
            />
            Create Posts from Template
          </label>
          <br />

          {/* Template Textarea for Create Template */}
          {createTemplate && (
            <label>
              Template Text:
              <textarea value={submittedData} onChange={(e) => setSubmittedData(e.target.value)} />
            </label>
          )}

          {/* Database ID Input and Template Radio Buttons for Create Posts from Template */}
          {!createTemplate && (
            <>
              <label>
                Database ID:
                <input type="text" value={databaseId} onChange={(e) => setDatabaseId(e.target.value)} />
              </label>
              <br />
              <label>
                Select Template:
                <select value={selectedTemplate} onChange={(e) => setSelectedTemplate(e.target.value)}>
                  <option value="" disabled>Select a template</option>
                  {templates.map((template) => (
                    <option key={template.temp1} value={template.data}>{template.data}</option>
                  ))}
                </select>
              </label>
              <br />
            </>
          )}

          {/* Submit Button */}
          <button type="submit">Submit</button>
        </form>
      </div>

      {/* Right Part - Display Results */}
      <div style={{ flex: '1', padding: '20px' }}>
        {/* Display Submitted Data or Generated Posts */}
        {createTemplate ? (
          <div>
            <h2>Created Template:</h2>
            <pre>{submittedData}</pre>
          </div>
        ) : (
          <div>
            <h2>Generated Posts:</h2>
            <ul>
              {generatedPosts.map((post, index) => (
                <li key={index}>{post}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default YourComponent;
