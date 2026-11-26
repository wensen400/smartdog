document.addEventListener("click", async (event) => {
  const likeBtn = event.target.closest(".like-btn");
  if (likeBtn) {
    event.preventDefault();
    await toggleLike(likeBtn);
    return;
  }

  const followBtn = event.target.closest(".follow-btn");
  if (followBtn) {
    event.preventDefault();
    await toggleFollow(followBtn);
  }
});

async function toggleLike(btn) {
  const postId = btn.dataset.postId;
  const res = await fetch(`/posts/${postId}/like`, { method: "POST" });
  if (res.status === 401) {
    window.location.href = "/auth/login";
    return;
  }
  const data = await res.json();
  const countEl = btn.querySelector(".count");
  if (countEl) countEl.textContent = data.count;
  btn.classList.toggle("liked", data.liked);
  btn.classList.toggle("text-amber-600", data.liked);
}

async function toggleFollow(btn) {
  const username = btn.dataset.username;
  const res = await fetch(`/users/${username}/follow`, { method: "POST" });
  if (res.status === 401) {
    window.location.href = "/auth/login";
    return;
  }
  const data = await res.json();
  const following = data.following;
  btn.textContent = following ? "已关注" : "关注";
  if (following) {
    btn.classList.remove("bg-amber-500", "text-white");
    btn.classList.add("bg-gray-200", "text-gray-700");
  } else {
    btn.classList.remove("bg-gray-200", "text-gray-700");
    btn.classList.add("bg-amber-500", "text-white");
  }
}
