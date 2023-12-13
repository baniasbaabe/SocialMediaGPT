import React, { useState, useEffect } from 'react';
import axios from 'axios';

import { useForm } from "react-hook-form";
import './notionform.css'

function NotionForm() {
    const [notionKey, setNotionKey] = useState('');
    const [openaiKey, setOpenaiKey] = useState('');
    const [createTemplate, setCreateTemplate] = useState(false);
    const [databaseId, setDatabaseId] = useState('');
    const [templates, setTemplates] = useState({ count: 0, data: [] })
    const [selectedTemplate, setSelectedTemplate] = useState('');
    const [generatedPosts, setGeneratedPosts] = useState([]);
    const [submittedData, setSubmittedData] = useState(null);
    const [generatedTemplate, setGeneratedTemplate] = useState({title: '', content: ''});
    const [isTemplatesFetched, setIsTemplatesFetched] = useState(false)
    const { register, formState: { errors }, handleSubmit } = useForm();

    const handleSubmitInner = async (data) => {
      if (createTemplate) {
        const response = await axios.post('http://localhost:8000/create_template',  {
          notionKey: notionKey,
          openaiKey: openaiKey,
          text: data.text,
          databaseId: databaseId,
          model: data.model
        }, { headers: {
          'Content-Type': 'application/json'
        }}).then(response => {
          setGeneratedTemplate(response.data)
          if (response.data.databaseId) {
          setDatabaseId(response.data.databaseId);}
        })
        .catch(error => alert('Error creating template. Please make sure to input valid Keys (and a valid Database ID). Check, if you have access to GPT-4 (if you selected it)'));
      }
      else{
        const response = await axios.post('http://localhost:8000/generate_posts', {
          notionKey: notionKey,
          openaiKey: openaiKey,
          databaseId: databaseId,
          templateText: selectedTemplate,
          model: data.model,
          numPosts: data.numPosts,
          topics: data.topics
        }, { headers: {
          'Content-Type': 'application/json'
      }}).then(response => {
        setGeneratedPosts(response.data)
      }).catch(error => alert('Error creating template. Please make sure to input valid Keys and a valid Database ID. Check, if you have access to GPT-4 (if you selected it)'));
      }
    }

    const handleFetchTemplates = () => {
      axios.get('http://localhost:8000/get_templates',
      {params: { notionKey: notionKey, databaseId: databaseId }, headers: {
        Accept: 'application/json',
        ContentType: "application/json"
    }})
        .then(response => {
          if (databaseId !== '' && notionKey !== '' && openaiKey !== '') {
          setTemplates(response.data);
          setIsTemplatesFetched(true)
        }
        else {
          alert('Please enter all the fields (NotionKey, OpenAIKey, DatabaseID).')}
        })
        .catch(error => alert(error));
    }


  return (
    <div className='row'>
        <div className='column'>
        <form id='myform' onSubmit={handleSubmit((data) => handleSubmitInner(data))}>
        <input type="text" required value={notionKey} onChange={(e) => setNotionKey(e.target.value)}></input>
          <br></br>
          <input type="text" required value={openaiKey} onChange={(e) => setOpenaiKey(e.target.value)} />
          <br></br>
          <label>
                Database ID:
                <input type="text" value={databaseId} onChange={(e) => setDatabaseId(e.target.value)} />
              </label>
          <br></br>
          <label>GPT-Model
          <select {...register("model")}>
          <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
          <option value="gpt-4">gpt-4</option>
        </select>
        <br></br>
        </label>
          <label>
            <input
              {...register("createTemplateOrPosts")}
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
            {...register("createTemplateOrPosts")}
              type="radio"
              name="operation"
              value="createPosts"
              checked={!createTemplate}
              onChange={() => setCreateTemplate(false)}
            />
            Create Posts from Template
          </label>
          <br />

          {createTemplate && (
            <label>
              Template Text:
              <textarea {...register("text")} />
            </label>
          )}

          {!createTemplate && (
            <>
            <button type='button' onClick={handleFetchTemplates}>Fetch your existing Templates</button>
            <br></br>
              {isTemplatesFetched && (
                <>
              <label>
                Select Template:
                <select value={selectedTemplate} onChange={(e) => setSelectedTemplate(e.target.value)}>
                  <option value="" disabled>Select a template</option>
                  {templates.data.map((template) => (
                    <option key={template.title} value={template.content}>{template.title}</option>
                  ))}
                </select>
                <br></br>
                <label for="numPosts">Quantity (between 1 and 5):</label>
                <input {...register("numPosts")} type="number" id="numPosts" name="numPosts" min="1" max="5" />
              </label>
              <br></br>
              <label>
                Topics, the posts should be about (separated by comma):
              <input {...register("topics")} type="text" required></input>
              </label>
               </>)}
            </>
          )}
        <br></br>
        <input form='myform' type="submit" />
        </form>
        </div>
        <div className='column'>
        {createTemplate ? (
          <div>
            <h2>Created Template:</h2>
            <pre>{generatedTemplate.title}</pre>
            <pre>{generatedTemplate.post}</pre>
          </div>
        ) : (
          <div>
            <h2>Generated Posts:</h2>
            {/* Check if selectedTemplate is not empty, if not then print it our */}
            {selectedTemplate && <pre>Selected Template: {selectedTemplate}</pre>}
            <ul>
              {generatedPosts.map((post, index) => (
                <li key={index}>{post.post}</li>
              ))}
            </ul>
          </div>
        )}
        </div>
    </div>
  )
}

export default NotionForm
