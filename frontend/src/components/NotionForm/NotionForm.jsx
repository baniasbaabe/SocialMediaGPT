import React, { useState } from "react";
import axios from "axios";

import { set, useForm } from "react-hook-form";
import "./notionform.css";

function NotionForm() {
  const [submitLoad, setSubmitLoad] = useState(false)
  const [fetchLoad, setFetchLoad] = useState(false)
  const [notionKey, setNotionKey] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [createTemplate, setCreateTemplate] = useState(true);
  const [databaseId, setDatabaseId] = useState("");
  const [pageId, setPageId] = useState("");
  const [templates, setTemplates] = useState({ count: 0, data: [] });
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [generatedPosts, setGeneratedPosts] = useState([]);
  const [generatedTemplate, setGeneratedTemplate] = useState({
    title: "",
    content: "",
  });
  const [isTemplatesFetched, setIsTemplatesFetched] = useState(false);
  const { register, handleSubmit } = useForm();

  const handleSubmitInner = async (data) => {
    if (createTemplate) {
      setSubmitLoad(true)
      const response = await axios
        .post(
          `${process.env.REACT_APP_API_URL}/create_template`,
          {
            notionKey: notionKey,
            openaiKey: openaiKey,
            text: data.text,
            databaseId: databaseId,
            model: data.model,
            pageId: pageId,
          },
          {
            headers: {
              "Content-Type": "application/json",
            },
          },
        )
        .then((response) => {
          setGeneratedTemplate(response.data);
          if (response.data.databaseId) {
            setDatabaseId(response.data.databaseId);
          }
        })
        .catch((error) =>
          alert(
            "Error creating template. Please make sure to input valid Keys (and a valid Database ID + Page ID). Check, if you have access to GPT-4 (if you selected it)",
          )).finally(() => setSubmitLoad(false));
    } else {
      setSubmitLoad(true)
      const response = await axios
        .post(
          `${process.env.REACT_APP_API_URL}/generate_posts`,
          {
            notionKey: notionKey,
            openaiKey: openaiKey,
            databaseId: databaseId,
            templateText: selectedTemplate,
            model: data.model,
            numPosts: data.numPosts,
            topics: data.topics,
          },
          {
            headers: {
              "Content-Type": "application/json",
            },
          },
        )
        .then((response) => {
          setGeneratedPosts(response.data);
        })
        .catch((error) =>
          alert(
            "Error creating template. Please make sure to input valid Keys and a valid Database ID. Check, if you have access to GPT-4 (if you selected it)",
          ),
        ).finally(() => setSubmitLoad(false));
    }
  };

  const handleFetchTemplates = () => {
    setFetchLoad(true)
    axios
      .post(`${process.env.REACT_APP_API_URL}/get_templates`, { notionKey: notionKey, databaseId: databaseId }, {
        headers: {
          "Accept": "application/json",
          "Content-Type": "application/json",
        },
      })
      .then((response) => {
        if (databaseId !== "" && notionKey !== "" && openaiKey !== "") {
          setTemplates(response.data);
          setIsTemplatesFetched(true);
        } else {
          alert(
            "Please enter all the fields (NotionKey, OpenAIKey, DatabaseID).",
          );
        }
      })
      .catch((error) => alert(error))
      .finally(() => setFetchLoad(false));
  };

  return (
    <div className="row">
      <div className="column">
        <div className="form-card-left">
          <form
            id="myform"
            onSubmit={handleSubmit((data) => handleSubmitInner(data))}
          >
            <label>
              Notion Key
              <input
                type="password"
                required
                value={notionKey}
                onChange={(e) => setNotionKey(e.target.value)}
              ></input>
            </label>
            <label>
              OpenAI Key
              <input
                type="password"
                required
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
              />
            </label>
            <label>
              Database ID
              <input
                type="text"
                value={databaseId}
                onChange={(e) => setDatabaseId(e.target.value)}
              />
            </label>
            <label>
              GPT-Model
              <select {...register("model")}>
                <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
                <option value="gpt-4">gpt-4</option>
              </select>
            </label>
            <label>
              <input
                {...register("createTemplateOrPosts")}
                type="radio"
                name="operation"
                value="createTemplate"
                checked={createTemplate}
                defaultChecked
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
                onChange={() => setCreateTemplate(false) || setIsTemplatesFetched(false)}
              />
              Create Posts from Template
            </label>

            {createTemplate && (
              <>
                <label>
                  Page ID (where Database should be created)
                  <input
                    type="text"
                    value={pageId}
                    onChange={(e) => setPageId(e.target.value)}
                  />
                </label>
                <label>
                  Post:
                  <textarea {...register("text")} />
                </label>
              </>
            )}

            {!createTemplate && (
              <>
                <button type="button" onClick={handleFetchTemplates} disabled={fetchLoad}>
                  Fetch Templates {fetchLoad && <i className="fa fa-spinner fa-spin fa-xs"></i>}
                </button>
                <br></br>
                {isTemplatesFetched && templates.count != 0 ? (
                  <>
                    <label>
                      Select Template:
                      <select
                        value={selectedTemplate}
                        onChange={(e) => setSelectedTemplate(e.target.value)}
                      >
                        <option value="" disabled>
                          Select a template
                        </option>
                        {templates.data.map((template) => (
                          <option key={template.title} value={template.content}>
                            {template.title}
                          </option>
                        ))}
                      </select>
                      <label for="numPosts">Quantity (between 1 and 5):</label>
                      <input
                        {...register("numPosts")}
                        type="number"
                        id="numPosts"
                        name="numPosts"
                        min="1"
                        max="5"
                        required
                      />
                    </label>
                    <label>
                      Topics, the posts should be about (separated by comma):
                      <input
                        {...register("topics")}
                        type="text"
                        required
                      ></input>
                    </label>
                  </>
                ) : (
                  <>
                    <p className="animated-templates-fetching-text">
                      {isTemplatesFetched ? "There aren't any templates in the database. Try again or create new templates." : "Templates are not yet fetched."}
                    </p>
                  </>
                )}
              </>
            )}
            <br></br>
            <button form="myform" type="submit" disabled={!createTemplate && templates.count === 0}>
            Submit {submitLoad && <i className="fa fa-spinner fa-spin fa-xs"></i>}
            </button>
          </form>
        </div>
      </div>
      <div className="column">
        <div className="form-card-right">
        {createTemplate ? (
          <div className="inner">
            <h2>Generated Template:</h2>
            <p>{generatedTemplate.title}</p>
            <p>{generatedTemplate.post}</p>
          </div>
        ) : (
          <div className="inner">
            <h2>Generated Posts:</h2>
            {selectedTemplate && (
              <p>Selected Template: <i>{selectedTemplate}</i></p>
              )}
              <hr></hr>
            <ul>
              {generatedPosts.map((post, index) => (
                <li key={index}>{post.post}</li>
              ))}
            </ul>
          </div>
        )}
        </div>

      </div>
    </div>
  );
}

export default NotionForm;
