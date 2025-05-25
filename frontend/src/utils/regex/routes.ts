const PRIVATE_ROUTES = [/dashboard.*/];
export const getIsPrivateRoute = (path: string) =>
  PRIVATE_ROUTES.some((route) => path.match(route));
