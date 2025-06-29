const PRIVATE_ROUTES = [/dashboard.*/];
export const getIsPrivateRoute = (path: string) =>
  PRIVATE_ROUTES.some((route) => path.match(route));

const NONLOGINROUTES = [/login.*/, /register.*/];
export const getNonLoginRoute = (path: string) =>
  NONLOGINROUTES.some((route) => path.match(route));
