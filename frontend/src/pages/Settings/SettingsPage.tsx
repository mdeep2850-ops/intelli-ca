import PlaceholderPage from '../../components/common/PlaceholderPage';
import { Settings } from 'lucide-react';

export default function SettingsPage() {
  return (
    <PlaceholderPage 
      title="Platform Settings"
      description="Configure integration keys, RAG distance thresholds, UI preferences, and user management."
      icon={Settings}
    />
  );
}
