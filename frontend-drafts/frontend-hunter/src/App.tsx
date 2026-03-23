import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/theme";
import { AppShell } from "@/components/layout";
import {
  DashboardPage,
  CollectionsPage,
  PracticePage,
  AssessmentFeedbackPage,
  ProgressPage,
} from "@/pages";

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/collections" element={<CollectionsPage />} />
            <Route path="/practice" element={<PracticePage />} />
            <Route path="/feedback" element={<AssessmentFeedbackPage />} />
            <Route path="/progress" element={<ProgressPage />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </ThemeProvider>
  );
}
