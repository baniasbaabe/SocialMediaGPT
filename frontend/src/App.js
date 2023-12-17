import './App.css';
import Navbar from './components/Navbar/Navbar';
import Hero from './components/Hero/Hero';
import NotionForm from './components/NotionForm/NotionForm';

function App() {
  return (
    <div className="App">
      <Navbar />
      <Hero />
      <NotionForm />
    </div>
  );
}

export default App;
