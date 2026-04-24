import MainPage from './pages/MainPage';
import { currentUser } from './services/mockData';

function App() {
    return <MainPage user={currentUser} />;
}

export default App;