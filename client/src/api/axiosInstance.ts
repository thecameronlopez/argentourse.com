import axios, {
  AxiosError,
  type AxiosRequestConfig,
  type AxiosResponse,
} from "axios";

export const client = (() => {
  return axios.create({
    baseURL: "http://127.0.0.1:8000/api/v1",
    withCredentials: true,
    headers: {
      "Content-Type": "application/json",
    },
  });
})();

export const request = async (options: AxiosRequestConfig) => {
  const onSuccess = (response: AxiosResponse) => {
    const { data } = response;
    return data;
  };

  const onError = function (error: AxiosError) {
    return Promise.reject({
      message: error.message,
      code: error.code,
      response: error.response,
    });
  };

  return client(options).then(onSuccess).catch(onError);
};
