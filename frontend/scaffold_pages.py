import os

pages = [
    'Landing/LandingPage', 'Auth/LoginPage', 'Dashboard/DashboardPage',
    'AIWorkspace/AIWorkspacePage', 'Documents/DocumentsPage',
    'FinancialTools/FinancialToolsPage', 'Clients/ClientsPage',
    'Reports/ReportsPage', 'Compliance/CompliancePage', 'Settings/SettingsPage'
]

for p in pages:
    folder, name = p.split('/')
    os.makedirs(f'src/pages/{folder}', exist_ok=True)
    with open(f'src/pages/{p}.tsx', 'w') as f:
        f.write(f'export default function {name}() {{\n  return <div>{name}</div>;\n}}\n')

os.makedirs('src/components/layout', exist_ok=True)
with open('src/components/layout/AppShell.tsx', 'w') as f:
    f.write('''import { Outlet } from 'react-router-dom';

export default function AppShell() {
  return (
    <div>
      <Outlet />
    </div>
  );
}
''')
