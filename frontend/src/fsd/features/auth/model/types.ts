export type LoginPayload = {
  username: string;
  password: string;
};

export type RegisterPayload = {
  username: string;
  email: string;
  password: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};
