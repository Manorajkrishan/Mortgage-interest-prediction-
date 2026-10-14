import { render, screen } from "@testing-library/react";
import App from "./App";

beforeEach(() => {
  global.fetch = jest.fn(() => Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ points: [], predictions: [], model: {} })
  }));
});

afterEach(() => jest.restoreAllMocks());

test("renders educational mortgage calculator and research warning", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: /understand the numbers/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /calculate repayment/i })).toBeInTheDocument();
  expect(screen.getByText(/independent educational tool/i)).toBeInTheDocument();
});
